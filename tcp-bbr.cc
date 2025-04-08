#include "tcp.h"
#include "flags.h"
#include "random.h"

// TCP BBR states
enum BbrState { STARTUP, DRAIN, PROBE_BW, PROBE_RTT };

class TcpBbrAgent : public TcpAgent {
public:
    TcpBbrAgent() : TcpAgent(), pacing_gain_(1.0), cwnd_gain_(2.0), max_bandwidth_(0.0),
                    min_rtt_(1e9), pacing_rate_(0.0), cwnd_(0), state_(STARTUP),
                    t_last_rtt_probe_(0.0), t_state_start_(0.0) {}

    virtual void sendmsg(int nbytes, const char *flags = 0) override;
    virtual void recv(Packet *pkt, Handler *h) override;
    virtual void timeout(int tno) override;

protected:
    double pacing_gain_;      // Pacing gain for rate control
    double cwnd_gain_;        // Congestion window gain
    double max_bandwidth_;    // Estimated bottleneck bandwidth (bytes/sec)
    double min_rtt_;          // Minimum observed RTT (seconds)
    double pacing_rate_;      // Current pacing rate (bytes/sec)
    int cwnd_;                // Congestion window (bytes)
    BbrState state_;          // Current BBR state
    double t_last_rtt_probe_; // Time of last RTT probe
    double t_state_start_;    // Time when current state started

    void update_max_bandwidth(double delivered, double rtt);
    void update_min_rtt(double rtt);
    bool bandwidth_growth_slows();
    int target_inflight();
    double cycle_gain();
    bool time_to_probe_rtt();
    bool rtt_stable_for_long_enough();
};

void TcpBbrAgent::sendmsg(int nbytes, const char *flags) {
    pacing_rate_ = pacing_gain_ * max_bandwidth_;
    TcpAgent::sendmsg(nbytes, flags);  // Call parent sendmsg
}

void TcpBbrAgent::recv(Packet *pkt, Handler *h) {
    double rtt = Scheduler::instance().clock() - hdr_tcp::access(pkt)->ts();
    int delivered = hdr_cmn::access(pkt)->size();

    // Update estimates
    update_max_bandwidth(delivered, rtt);
    update_min_rtt(rtt);

    // Update state start time when transitioning
    if (state_ != PROBE_RTT) t_state_start_ = Scheduler::instance().clock();

    // BBR state machine
    switch (state_) {
        case STARTUP:
            if (bandwidth_growth_slows()) {
                state_ = DRAIN;
                t_state_start_ = Scheduler::instance().clock();
            }
            break;
        case DRAIN:
            if (cwnd_ <= target_inflight()) {  // Approximate inflight with cwnd_
                state_ = PROBE_BW;
                t_state_start_ = Scheduler::instance().clock();
            }
            break;
        case PROBE_BW:
            pacing_gain_ = cycle_gain();
            if (time_to_probe_rtt()) {
                state_ = PROBE_RTT;
                t_last_rtt_probe_ = Scheduler::instance().clock();
                t_state_start_ = Scheduler::instance().clock();
            }
            break;
        case PROBE_RTT:
            cwnd_ = 4 * size_;  // Minimum cwnd (e.g., 4 packets)
            if (rtt_stable_for_long_enough()) {
                state_ = PROBE_BW;
                t_state_start_ = Scheduler::instance().clock();
            }
            break;
    }

    // Update congestion window
    cwnd_ = cwnd_gain_ * (max_bandwidth_ * min_rtt_);
    if (cwnd_ < size_) cwnd_ = size_;  // Minimum cwnd

    TcpAgent::recv(pkt, h);  // Call parent recv
}

void TcpBbrAgent::timeout(int tno) {
    TcpAgent::timeout(tno);  // Handle timeouts as in base class
}

void TcpBbrAgent::update_max_bandwidth(double delivered, double rtt) {
    double bw = delivered / rtt;
    if (bw > max_bandwidth_) max_bandwidth_ = bw;
}

void TcpBbrAgent::update_min_rtt(double rtt) {
    if (rtt < min_rtt_) min_rtt_ = rtt;
}

bool TcpBbrAgent::bandwidth_growth_slows() {
    // Simplified: Assume growth slows after initial burst
    return (max_bandwidth_ > 0 && cwnd_ > 10 * size_);
}

int TcpBbrAgent::target_inflight() {
    return max_bandwidth_ * min_rtt_;  // BDP (bandwidth-delay product)
}

double TcpBbrAgent::cycle_gain() {
    static int cycle = 0;
    cycle = (cycle + 1) % 8;
    if (cycle == 0) return 1.25;  // Probe up
    if (cycle == 1) return 0.75;  // Probe down
    return 1.0;                   // Steady state
}

bool TcpBbrAgent::time_to_probe_rtt() {
    // Probe RTT every 10 seconds (simplified)
    return (Scheduler::instance().clock() - t_last_rtt_probe_ > 10.0);
}

bool TcpBbrAgent::rtt_stable_for_long_enough() {
    // Simplified: Assume stable after 200ms in PROBE_RTT
    return (Scheduler::instance().clock() - t_state_start_ > 0.2);
}

// Register the new agent with Tcl
static class TcpBbrClass : public TclClass {
public:
    TcpBbrClass() : TclClass("Agent/TCP/Bbr") {}
    TclObject* create(int, const char*const*) {
        return (new TcpBbrAgent());
    }
} class_tcp_bbr;
