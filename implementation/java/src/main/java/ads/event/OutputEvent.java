package ads.event;

/**
 * Actuator commands emitted (as transition actions) by the ADS
 * supervisory state machine. Each {@code actuator.apply(new OutputEvent.X())}
 * call is extracted by the M2M as a RoboChart event communication.
 *
 * <ul>
 *   <li>{@code RaiseAlarm} — annunciate the outlet-dewpoint alarm (REQ-ADS-003).</li>
 *   <li>{@code StartChangeover} — command the changeover valve set to swap
 *       beds (REQ-ADS-006).</li>
 *   <li>{@code EnterFailSafe} — command the fail-safe state on power loss
 *       (REQ-ADS-007).</li>
 *   <li>{@code RestoreNormal} — command the return to normal operation on
 *       backup-supply recovery (REQ-ADS-007).</li>
 * </ul>
 */
public sealed interface OutputEvent {

    /** raiseAlarm — annunciate the dewpoint alarm. */
    record RaiseAlarm() implements OutputEvent {
    }

    /** startChangeover — swap to the standby dryer bed. */
    record StartChangeover() implements OutputEvent {
    }

    /** enterFailSafe — drive the plant to the fail-safe state. */
    record EnterFailSafe() implements OutputEvent {
    }

    /** restoreNormal — resume normal detritiation. */
    record RestoreNormal() implements OutputEvent {
    }
}
