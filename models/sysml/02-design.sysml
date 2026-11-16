package ADSDesign {
    doc
    /*
     * Design model for an Atmosphere Detritiation System (ADS) worked example. Defines the process train that removes tritium from facility air before discharge to stack, and maps each design element to the requirement it satisfies (see ADSRequirements).
     */
    private import 'ADS Requirements'::*;
    private import ScalarValues::*;
    item def TritiatedAir {
        doc
        /*
         * Facility room air carrying tritium as HT gas and HTO vapour. This is the medium the ADS processes: the recombiner oxidises HT to HTO, which is then removed as moisture.
         */
        attribute tritiumActivity : ScalarValues::Real;
        attribute humidity : ScalarValues::Real;
    }
    part def AtmosphereDetritiationSystem {
        doc
        /*
         * The complete ADS process train.
         */
    }
    part def CirculationBlower {
        doc
        /*
         * Draws contaminated room air through the process train at the design volumetric flow rate.
         */
        attribute flowRate : ScalarValues::Real;
    }
    port def AirPort {
        doc
        /*
         * Process-air interface carrying TritiatedAir through the ADS train. The owner receives air through the 'in' item; emitting ends use the conjugated form ~AirPort.
         */
        out item air : TritiatedAir;
    }
    interface def AirInterface {
        end port supplierPort : AirPort;
        end port consumerPort : ~AirPort;
        flow of TritiatedAir from supplierPort to consumerPort;
    }
    part def CatalyticRecombiner {
        doc
        /*
         * Heated catalyst bed that oxidises elemental tritium (HT) to tritiated water vapour (HTO) so it can be captured as moisture downstream. Conversion efficiency drives the achievable DF.
         */
        attribute bedTemperature : ScalarValues::Real;
        attribute conversionEfficiency : ScalarValues::Real;
    }
    part def Condenser {
        doc
        /*
         * Bulk moisture removal stage: cools the gas stream to condense HTO vapour ahead of the dryers. regenReturn receives the wet regeneration stream from the off-line dryer bed, keeping regeneration effluent inside the process boundary.
         */
        attribute outletTemperature : ScalarValues::Real;
    }
    enum def Dryer {
        BedA;
        BedB;
    }
    part def MolecularSieveDryer {
        doc
        /*
         * Adsorption bed that captures residual HTO down to the required outlet dewpoint. Two beds (A/B) alternate between drying duty and regeneration; bedSaturation tracks remaining capacity.
         */
        attribute bedSaturation : ScalarValues::Real = 50;
        attribute dewpointOut : ScalarValues::Real;
        attribute saturationTimeConstant : ScalarValues::Real = 4000 {
            doc
            /*
             * Bed saturation time constant in seconds: the decontamination factor of a bed on duty decays as exp(-t/saturationTimeConstant) as the sieve loads with moisture. Bound by value to the parameter tSat of the ADSChangeover simulation (sim-binding).
             */
        }
    }
    part def ChangeoverValveSet {
        doc
        /*
         * Valve group that redirects process flow between dryer beds so a saturated bed can regenerate without interrupting detritiation.
         */
        attribute position : ScalarValues::Real;
    }
    part def DewpointMonitor {
        doc
        /*
         * Measures dryer outlet dewpoint; a high reading signals bed saturation and triggers changeover. Subject to a defined calibration interval.
         */
        attribute dewpoint : ScalarValues::Real = -60;
        attribute calibrationDue : ScalarValues::Real;
    }
    part def TritiumStackMonitor {
        doc
        /*
         * Independent measurement of tritium release rate at the stack - deliberately not part of the ADS control loop, so discharge accounting cannot be corrupted by a control failure.
         */
        attribute releaseRate : ScalarValues::Real = 200;
    }
    part def ADSController {
        doc
        /*
         * Sequences dryer changeover and commands the fail-safe state on loss of power or instrument fault. activeDryer records which bed is on duty.
         */
        attribute activeDryer : Dryer = Dryer::BedA;
        attribute upsState : ScalarValues::Boolean;
        attribute changeoverPeriod : ScalarValues::Real = 7000 {
            doc
            /*
             * Changeover period in seconds: the controller swaps the duty bed for the fresh standby bed every changeoverPeriod. Bound by value to the parameter tCycle of the ADSChangeover simulation (sim-binding), which takes its value from here.
             */
        }
    }
    part def UPSBackupSupply {
        doc
        /*
         * Battery-backed supply that keeps the controller, valves and monitors alive through a loss of normal power so the system can reach and hold its fail-safe state.
         */
        attribute charge : ScalarValues::Real;
    }
    part ads : AtmosphereDetritiationSystem {
        doc
        /*
         * The installed ADS plant: blower -> recombiner -> condenser -> duty dryer -> stack, with a redundant dryer bed on regeneration. The flow connections model the air path; the satisfy statements allocate each ADSRequirements requirement to the design element that meets it.
         */
        in port plantAirIn : AirPort;
        out port stackOut : ~AirPort;
        part blower : CirculationBlower {
            in port airIn : AirPort;
            out port airOut : ~AirPort;
        }
        part condenser : Condenser {
            in port regenReturn : AirPort;
            in port airIn : AirPort;
            out port airOut : ~AirPort;
        }
        part recombiner : CatalyticRecombiner {
            in port airIn : AirPort;
            out port airOut : AirPort;
        }
        part dryerA : MolecularSieveDryer {
            in port airIn : AirPort;
            out port regenOut : ~AirPort;
            out port airOut : ~AirPort;
        }
        part dryerB : MolecularSieveDryer {
            in port airIn : AirPort;
            out port airOut : ~AirPort;
            out port regenOut : ~AirPort;
        }
        part changeoverValves : ChangeoverValveSet {
            in port airIn : AirPort;
            out port outletB : ~AirPort;
            out port outletA : ~AirPort;
        }
        part dewpointMonitor : DewpointMonitor {
            in port sample : AirPort;
        }
        part stackMonitor : TritiumStackMonitor {
            in port sample : AirPort;
        }
        part backupSupply : UPSBackupSupply;
        flow of TritiatedAir from plantAirIn to airIn;
        flow of TritiatedAir from airOut to stackOut;
        flow of TritiatedAir from airOut to stackOut;
        interface blowerToRecombiner : AirInterface connect airOut to airIn;
        interface recombinerToCondenser : AirInterface connect airOut to airIn;
        interface condenserToValves : AirInterface connect airOut to airIn;
        interface valvesToDryerA : AirInterface connect outletA to airIn;
        interface valvesToDryerB connect outletB to airIn;
        interface dryerARegenReturn connect regenOut to regenReturn;
        interface interfaceEdge connect regenOut to regenReturn;
        interface stackSample connect stackOut to sample;
        interface dryerBSample connect airOut to sample;
        interface dryerASample connect airOut to sample;
        part controller : ADSController {
            doc
            /*
             * Runs the ADSOperation state machine that governs changeover and fail-safe behaviour.
             */
        }
    }
    satisfy dischargeLimit by ads;
    satisfy detritiationAvailability by backupSupply;
    satisfy detritiationCapacity by ads;
    satisfy changeoverContinuity by changeoverValves;
    satisfy monitoringAndAlarm by dewpointMonitor;
    satisfy recombinerEfficiency by recombiner;
    satisfy dryerCapacityMargin by dryerA;
    satisfy dryerRedundancy by controller;
    satisfy lossOfPowerResponse by backupSupply;
    satisfy stackMonitorIndependence by stackMonitor;
    satisfy regenerationContainment by condenser;
    satisfy changeoverProofTest by controller;
    satisfy dewpointAccuracy by dewpointMonitor;
    satisfy detritiationCapacity by blower;
    satisfy dryerCapacityMargin by dryerB;
    satisfy dryerRedundancy by dryerA;
    satisfy dryerRedundancy by dryerB;
    state def ADSOperation {
        doc
        /*
         * Operating modes of the ADS: continuous detritiation (NormalOperation), dryer bed swap (Changeover), and the safe shutdown state entered on power loss (FailSafe).
         */
        ref state start :>> States::StateAction::start;
        state NormalOperation;
        state Changeover;
        state FailSafe;
        attribute dewpoint : ScalarValues::Real;
        attribute dewpointLimit : ScalarValues::Real;
        attribute changeoverComplete : ScalarValues::Boolean;
        attribute powerAvailable : ScalarValues::Boolean;
        action swapDutyBed {
            doc
            /*
             * Hands duty to the standby bed: activeDryer becomes the bed that was regenerated during changeover.
             */
        }
        transition first start then NormalOperation;
        transition normal_to_changeover first NormalOperation accept when dewpoint > dewpointLimit then Changeover;
        transition normal_to_failsafe first NormalOperation accept when not powerAvailable then FailSafe;
        transition changeover_to_failsafe first Changeover accept when not powerAvailable then FailSafe;
        transition failsafe_recovery first FailSafe accept when powerAvailable then NormalOperation;
        transition changeover_complete first Changeover accept when changeoverComplete do swapDutyBed then NormalOperation;
    }
}
