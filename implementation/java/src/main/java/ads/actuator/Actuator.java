package ads.actuator;

import ads.event.OutputEvent;
import java.util.ArrayList;
import java.util.List;

/**
 * Output sink for the commands emitted by the ADS supervisory state
 * machine (alarm, changeover, fail-safe, restore). Each
 * {@code apply(new OutputEvent.X())} call is extracted by the M2M as a
 * RoboChart event communication.
 */
public final class Actuator {

    private OutputEvent last;
    private final List<OutputEvent> history = new ArrayList<>();

    public void apply(OutputEvent command) {
        this.last = command;
        history.add(command);
    }

    /** Every command applied so far, in order. */
    public List<OutputEvent> history() {
        return List.copyOf(history);
    }

    public OutputEvent last() {
        return last;
    }
}
