package 'ADS Requirements' {
    doc
    /*
     * Requirements for the Atmosphere Detritiation System
     */
    requirement def RadiologicalReleaseLimit {
        doc
        /*
         * Routine tritium discharge to atmosphere shall remain within the authorised annual limit and be reduced ALARP.
         */
    }
    requirement <'REQ-TRIT-014'> dischargeLimit : RadiologicalReleaseLimit {
        doc
        /*
         * * Routine tritium discharge to the atmosphere via the ADS stack shall remain within the authorised annual limit and be reduced as low as reasonably practicable (ALARP).
         */
    }
    requirement <'REQ-TRIT-007'> confinementIntegrity {
        doc
        /*
         * At least two independent confinement barriers shall be maintained between tritium inventory and the environment under all credible conditions.
         */
    }
    requirement <'REQ-TRIT-021'> inventoryCap {
        doc
        /*
         * The tritium inventory held in any single processing location shall not exceed the authorised cap.
         */
    }
    requirement <'REQ-TRIT-030'> detritiationAvailability {
        doc
        /*
         * Atmosphere detritiation shall remain available in all plant states, including loss of off-site power.
         */
    }
    requirement <'REQ-ADS-001'> detritiationCapacity : RadiologicalReleaseLimit {
        doc
        /*
         * The ADS shall achieve a decontamination factor of at least 1000 for tritiated species at design-basis flow.
         */
        attribute minDecontaminationFactor : ScalarValues::Real = 1000 {
            doc
            /*
             * The minimum decontamination factor this requirement sets (dimensionless). Bound by value to the parameter DFtarget of the ADSChangeover simulation (sim-binding), whose assertion checks DF >= DFtarget.
             */
        }
    }
    requirement <'REQ-ADS-002'> changeoverContinuity {
        doc
        /*
         * Dryer-bed changeover shall complete without loss of the detritiation function.
         */
    }
    requirement <'REQ-ADS-003'> monitoringAndAlarm {
        doc
        /*
         * Outlet dewpoint and stack tritium activity shall be continuously monitored with alarm thresholds.
         */
    }
    requirement <'REQ-ADS-004'> recombinerEfficiency {
        doc
        /*
         * The catalytic recombiner shall convert at least 99.9% of elemental tritium (HT) to HTO at operating temperature.
         */
    }
    requirement <'REQ-ADS-005'> dryerCapacityMargin {
        doc
        /*
         * A single molecular-sieve bed shall hold at least 24 hours of design-basis moisture load before breakthrough.
         */
    }
    requirement <'REQ-ADS-006'> dryerRedundancy {
        doc
        /*
         * Two independent dryer beds shall be provided, with automatic changeover initiated on dewpoint alarm.
         */
    }
    requirement <'REQ-ADS-007'> lossOfPowerResponse {
        doc
        /*
         * On loss of off-site power the ADS shall enter a fail-safe state and restart on the backup supply within 30 seconds.
         */
    }
    requirement <'REQ-ADS-008'> stackMonitorIndependence {
        doc
        /*
         * Stack tritium monitoring shall be independent of the ADS process-control system. ss
         */
    }
    requirement <'REQ-ADS-009'> regenerationContainment {
        doc
        /*
         * Tritiated water desorbed during bed regeneration shall be routed to the tritiated-water collection system, never to the stack.
         */
    }
    requirement <'REQ-ADS-010'> changeoverProofTest {
        doc
        /*
         * The changeover logic shall be periodically testable without taking the ADS out of service.
         */
    }
    requirement <'REQ-ADS-011'> dewpointAccuracy {
        doc
        /*
         * Outlet dewpoint shall be measured within +/-2 degrees C with a defined calibration interval.
         */
    }
}
