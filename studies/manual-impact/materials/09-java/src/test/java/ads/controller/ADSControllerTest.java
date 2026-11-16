package ads.controller;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ads.actuator.Actuator;
import ads.datamodel.Dryer;
import ads.event.InputEvent;
import ads.event.OutputEvent;
import ads.mode.ADSMode;
import ads.sensor.DryerFunctions;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Behavioural tests for {@link ADSController} — the software realisation of
 * the {@code ADSOperation} state machine in {@code 02-design.sysml}.
 *
 * <p>These tests exercise the same safety properties the Dafny and Isabelle
 * models prove abstractly, at the level of the running implementation, so the
 * proof and the code are checked against one contract:</p>
 * <ul>
 *   <li><b>REQ-ADS-002</b> — exactly one dryer bed is active at all times
 *       (the detritiation function is never lost across a changeover).</li>
 *   <li><b>REQ-ADS-006</b> — a dewpoint alarm initiates a bed changeover and
 *       the beds alternate.</li>
 *   <li><b>REQ-ADS-007</b> — loss of off-site power drives the plant to
 *       FailSafe from any mode, and FailSafe is only left on backup-restored
 *       (matches Isabelle lemma R1).</li>
 * </ul>
 */
class ADSControllerTest {

    private Actuator actuator;
    private ADSController controller;

    @BeforeEach
    void setUp() {
        actuator = new Actuator();
        controller = new ADSController(new DryerFunctions(), actuator);
    }

    // ── Initial state ──────────────────────────────────────────────────────

    @Test
    @DisplayName("Starts in NormalOperation on bed A")
    void startsInNormalOperationOnBedA() {
        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedA, controller.activeDryer());
    }

    // ── Changeover sequence (REQ-ADS-002, REQ-ADS-006) ─────────────────────

    @Test
    @DisplayName("DewpointHigh requests changeover and commands StartChangeover")
    void dewpointHighStartsChangeover() {
        controller.step(new InputEvent.DewpointHigh());

        assertEquals(ADSMode.Changeover, controller.currentMode());
        // RaiseAlarm then StartChangeover are emitted, in that order.
        assertEquals(List.of(OutputEvent.RaiseAlarm.class, OutputEvent.StartChangeover.class),
                actuator.history().stream().map(Object::getClass).toList());
        assertInstanceOf(OutputEvent.StartChangeover.class, actuator.last());
        // The bed does not swap until the changeover *completes*.
        assertEquals(Dryer.BedA, controller.activeDryer());
    }

    @Test
    @DisplayName("ChangeoverComplete alternates the active bed and returns to NormalOperation")
    void changeoverCompleteAlternatesBedAndReturnsToNormal() {
        controller.step(new InputEvent.DewpointHigh());
        controller.step(new InputEvent.ChangeoverComplete());

        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedB, controller.activeDryer());
    }

    @Test
    @DisplayName("Two successive changeovers return the active bed to A (alternation)")
    void twoChangeoversReturnToBedA() {
        for (int i = 0; i < 2; i++) {
            controller.step(new InputEvent.DewpointHigh());
            controller.step(new InputEvent.ChangeoverComplete());
        }
        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedA, controller.activeDryer());
    }

    @Test
    @DisplayName("A second DewpointHigh during Changeover is ignored (no double changeover)")
    void changeoverIgnoresDewpointHigh() {
        controller.step(new InputEvent.DewpointHigh());
        controller.step(new InputEvent.DewpointHigh());

        assertEquals(ADSMode.Changeover, controller.currentMode());
        assertEquals(Dryer.BedA, controller.activeDryer());
    }

    // ── Fail-safe on power loss (REQ-ADS-007) ──────────────────────────────

    @Test
    @DisplayName("PowerLoss from NormalOperation enters FailSafe")
    void powerLossFromNormalEntersFailSafe() {
        controller.step(new InputEvent.PowerLoss());

        assertEquals(ADSMode.FailSafe, controller.currentMode());
        assertInstanceOf(OutputEvent.EnterFailSafe.class, actuator.last());
    }

    @Test
    @DisplayName("PowerLoss from Changeover also enters FailSafe (override from any mode)")
    void powerLossFromChangeoverEntersFailSafe() {
        controller.step(new InputEvent.DewpointHigh());
        controller.step(new InputEvent.PowerLoss());

        assertEquals(ADSMode.FailSafe, controller.currentMode());
        assertInstanceOf(OutputEvent.EnterFailSafe.class, actuator.last());
    }

    @Test
    @DisplayName("BackupRestored leaves FailSafe and commands RestoreNormal")
    void backupRestoredFromFailSafeReturnsToNormal() {
        controller.step(new InputEvent.PowerLoss());
        controller.step(new InputEvent.BackupRestored());

        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertInstanceOf(OutputEvent.RestoreNormal.class, actuator.last());
    }

    @Test
    @DisplayName("FailSafe is only left on BackupRestored (Isabelle R1)")
    void failSafeOnlyExitsOnBackupRestored() {
        controller.step(new InputEvent.PowerLoss());

        // None of these may move the plant out of FailSafe.
        controller.step(new InputEvent.DewpointHigh());
        assertEquals(ADSMode.FailSafe, controller.currentMode());
        controller.step(new InputEvent.ChangeoverComplete());
        assertEquals(ADSMode.FailSafe, controller.currentMode());
        controller.step(new InputEvent.PowerLoss());
        assertEquals(ADSMode.FailSafe, controller.currentMode());
    }

    // ── Spurious events are ignored ────────────────────────────────────────

    @Test
    @DisplayName("Spurious ChangeoverComplete / BackupRestored in NormalOperation are ignored")
    void normalOperationIgnoresSpuriousEvents() {
        controller.step(new InputEvent.ChangeoverComplete());
        controller.step(new InputEvent.BackupRestored());

        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedA, controller.activeDryer());
    }

    // ── Continuity invariant (REQ-ADS-002): exactly one live bed, always ───

    @Test
    @DisplayName("Exactly one dryer bed is active after every event (REQ-ADS-002)")
    void exactlyOneDryerActiveThroughout() {
        InputEvent[] sequence = {
            new InputEvent.DewpointHigh(),
            new InputEvent.ChangeoverComplete(),   // → BedB
            new InputEvent.PowerLoss(),            // → FailSafe
            new InputEvent.BackupRestored(),       // → Normal (BedB)
            new InputEvent.DewpointHigh(),
            new InputEvent.ChangeoverComplete(),   // → BedA
            new InputEvent.DewpointHigh(),
            new InputEvent.PowerLoss(),            // → FailSafe mid-changeover
        };
        for (InputEvent e : sequence) {
            controller.step(e);
            Dryer d = controller.activeDryer();
            assertNotNull(d, "active dryer must never be null");
            assertTrue(d == Dryer.BedA || d == Dryer.BedB,
                "exactly one bed (A or B) must be active at all times");
        }
    }

    // ── End-to-end choreography matching the digital-twin demo ─────────────

    @Test
    @DisplayName("Full choreography: Normal → Changeover → Normal(B) → FailSafe → Normal(B)")
    void fullChoreography() {
        controller.step(new InputEvent.DewpointHigh());
        assertEquals(ADSMode.Changeover, controller.currentMode());

        controller.step(new InputEvent.ChangeoverComplete());
        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedB, controller.activeDryer());

        controller.step(new InputEvent.PowerLoss());
        assertEquals(ADSMode.FailSafe, controller.currentMode());

        controller.step(new InputEvent.BackupRestored());
        assertEquals(ADSMode.NormalOperation, controller.currentMode());
        assertEquals(Dryer.BedB, controller.activeDryer(), "bed selection survives the fail-safe cycle");
    }
}
