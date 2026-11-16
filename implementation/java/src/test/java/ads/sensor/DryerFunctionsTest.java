package ads.sensor;

import static org.junit.jupiter.api.Assertions.assertEquals;

import ads.datamodel.Dryer;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Tests for {@link DryerFunctions#nextDryer(Dryer)} — the pure changeover
 * selection function. Alternation (and its involution property) is what
 * guarantees the two-bed redundancy of REQ-ADS-006 and underwrites the
 * "exactly one live bed" continuity invariant of REQ-ADS-002.
 */
class DryerFunctionsTest {

    private final DryerFunctions dryers = new DryerFunctions();

    @Test
    @DisplayName("nextDryer alternates A → B and B → A")
    void nextDryerAlternates() {
        assertEquals(Dryer.BedB, dryers.nextDryer(Dryer.BedA));
        assertEquals(Dryer.BedA, dryers.nextDryer(Dryer.BedB));
    }

    @Test
    @DisplayName("nextDryer is an involution: applying it twice is the identity")
    void nextDryerIsInvolution() {
        for (Dryer d : Dryer.values()) {
            assertEquals(d, dryers.nextDryer(dryers.nextDryer(d)));
        }
    }
}
