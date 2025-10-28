import sys

class Logger:
    def __init__(self, color=True) -> None:
        if color:
            self.info = "\x1b[0;30;44m [INFO] \x1b[0m "
            self.warn = "\x1b[0;30;43m [WARNING] \x1b[0m "
            self.error = "\x1b[0;30;41m [ERROR] \x1b[0m "
            self.success = "\x1b[0;30;42m [SUCCESS] \x1b[0m "
            self.pointer = "\x1b[5;36;40m>>>\x1b[0m "
            self.ask = "\x1b[0;30;46m ? \x1b[0m "
            self.welcome = (
                "\n\x1b[0;30;46m                              \x1b[0m\n"
                + "\x1b[0;30;46m  \x1b[0m                          \x1b[0;30;46m  \x1b[0m\n"
                + "\x1b[0;30;46m  \x1b[0m  \x1b[0;36;40mWelcome to resomapper!\x1b[0m  "
                + "\x1b[0;30;46m  \x1b[0m\n"
                + "\x1b[0;30;46m  \x1b[0m                          \x1b[0;30;46m  \x1b[0m\n"
                + "\x1b[0;30;46m                              \x1b[0m\n"
            )
            self.new_patient1 = "\x1b[0;30;47m * STUDY *  "
            self.new_patient2 = " * STUDY * \x1b[0m "
            self.new_modal = "\x1b[0;30;47m > MODAL > \x1b[0m "
        else:
            self.info = "[[INFO]] "
            self.warn = "[[WARNING]] "
            self.error = "[[ERROR]] "
            self.success = "[[SUCCESS]] "
            self.pointer = ">>> "
            self.ask = "[[?]] "
            self.welcome = (
                "\n------------------------------\n"
                + "--                          --\n"
                + "--  Welcome to resomapper!  --\n"
                + "--                          --\n"
                + "------------------------------\n\n"
            )
            self.new_patient1 = " * STUDY *  "
            self.new_patient2 = " * STUDY *  "
            self.new_modal = " > MODAL > "

def auto_init_logger():
    if sys.stdout.isatty():
        return Logger(color=True)
    else:
        return Logger(color=False)
    
auto_innited_logger = auto_init_logger()

#### OTHER DICTS ####

acq_categories_BIDS = {
    "localizer": "anat",
    "T2w": "anat",
    "T1w": "anat",
    "T1map_acq": "anat",
    "T2map_acq": "anat",
    "T2starmap_acq": "anat",
    "MTon": "anat",
    "MToff": "anat",
    "fmap": "fmap",
    "dwi": "dwi",
    "dce": "perf",
    "etc": "etc",
}

conditions_dict_bruker = {
    "T2w": [lambda params: params["scan_method"] == "Bruker:RARE"],
    "T1w": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: "T1" in params["seq_name"],
    ],
    "localizer": [
        lambda params: params["scan_method"] == "Bruker:FLASH"
        and "localiz" in params["seq_name"].lower()
    ],
    "dwi": [lambda params: params["scan_method"] == "Bruker:DtiEpi"],
    "T2map_acq": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "Off",
        lambda params: isinstance(params["echo_time"], list),
    ],
    "T2starmap_acq": [lambda params: params["scan_method"] == "Bruker:MGE"],
    "T1map_acq": [lambda params: params["scan_method"] == "Bruker:RAREVTR"],
    "MTon": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "On",
    ],
    "MToff": [
        lambda params: params["scan_method"] == "Bruker:MSME",
        lambda params: params["mt_on_off"] == "Off",
        lambda params: not isinstance(params["echo_time"], list),
    ],
    "fmap": [lambda params: params["scan_method"] == "Bruker:FieldMap"],
    "dce": [
        lambda params: params["scan_method"] == "Bruker:FLASH"
        and "dce" in params["seq_name"].lower()
    ],
}

conditions_dict_MRS = {
    "T2w": [lambda params: "fse" in params["seq_name"].lower()],
    "T1w": [
        lambda params: "se" in params["seq_name"].lower(),
        lambda params: "t1" in params["seq_name"].lower(),
        lambda params: "map" not in params["seq_name"].lower(),
    ],
    "localizer": [lambda params: "scout" in params["seq_name"].lower()],
    "dwi": [
        lambda params: "epi" in params["seq_name"].lower(),
        lambda params: "dti" in params["seq_name"].lower(),
        lambda params: "pre" not in params["seq_name"].lower(),
    ],
    "T2map_acq": [lambda params: "mems" in params["seq_name"].lower()],
    "T2starmap_acq": [lambda params: "mge" in params["seq_name"].lower()],
    "T1map_acq": [
        lambda params: "se" in params["seq_name"].lower(),
        lambda params: "t1" in params["seq_name"].lower(),
        lambda params: "map" in params["seq_name"].lower(),
    ],
    # "MTon": [...],
    # "MToff": [...],
    # "fmap": [...],
    "dce": [lambda params: "dce" in params["seq_name"].lower()],
}

metadata_ref_BIDS_bruker = {
    #### "Subject" #### 
    #### "HardwareInformation" #### 
    "Manufacturer": "VisuManufacturer",
    "ManufacturersModelName": "VisuStation",
    "DeviceSerialNumber": "VisuSystemOrderNumber",
    "StationName": "VisuStation",
    "SoftwareVersion": "VisuAcqSoftwareVersion",
    "MagneticFieldStrength": {
        "Equation": "Freq / 42.576",
        "Freq": "VisuAcqImagingFrequency",
    },
    # "ReceiveCoilActiveElements": "VisuCoilReceiveType",
    # "ReceiveCoilName": "VisuCoilReceiveName",
    # "GradientSetType": "ACQ_status",
    # "MRTransmitCoilSequence": {
    #     "Manufacture": "VisuCoilTransmitManufacturer",
    #     "Name": "VisuCoilTransmitName",
    #     "Type": "VisuCoilTransmitType",
    # },
    "MatrixCoilMode": "ACQ_experiment_mode",
    ##### "InstitutionInformation" #### 
    "InstitutionName": "VisuInstitution",
    ##### "SequenceSpecifics" #### 
    "PulseSequenceDetails": "ACQ_scan_name",
    "PulseSequenceType": "PULPROG",
    "ScanningSequence": "VisuAcqSequenceName",
    "SequenceName": ["VisuAcquisitionProtocol", "ACQ_protocol_name"],
    "SequenceVariant": "VisuAcqEchoSequenceType",
    "ScanOptions": {
        "CG": "VisuCardiacSynchUsed",
        "FC": "VisuAcqFlowCompensation",
        "FP": "VisuAcqSpectralSuppression",
        "PFF": {"idx": 0, "key": "VisuAcqPartialFourier"},
        "PFP": {"idx": 1, "key": "VisuAcqPartialFourier"},
        "RG": "VisuRespSynchUsed",
        "SP": "PVM_FovSatOnOff",
    },
    "NonlinearGradientCorrection": "VisuAcqKSpaceTraversal",
    ##### "SpatialEncoding" ####
    "EffectiveEchoSpacing": {
        "ACCfactor": "ACQ_phase_factor",
        "BWhzPixel": "VisuAcqPixelBandwidth",
        "Equation": "(1 / (MatSizePE * BWhzPixel)) / " "ACCfactor",
        "MatSizePE": {
            "idx": [
                {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
                {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
            ],
            "key": "VisuCoreSize",
        },
    },
    "NumberShots": "VisuAcqKSpaceTrajectoryCnt",
    "ParallelReductionFactorInPlane": "ACQ_phase_factor",
    "PartialFourier": "VisuAcqPartialFourier",
    "PhaseEncodingDirection": [
        {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
        {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
    ],
    "TotalReadoutTime": {
        "ACCfactor": "ACQ_phase_factor",
        "BWhzPixel": "VisuAcqPixelBandwidth",
        "ETL": "VisuAcqEchoTrainLength",
        "Equation": "(1 / BWhzPixel) / ACCfactor",
    },
    ##### "TimingParameters" #### 
    "DwellTime": {"BWhzPixel": "VisuAcqPixelBandwidth", "Equation": "1/BWhzPixel"},
    "EchoTime": "VisuAcqEchoTime",
    "RepetitionTime": "VisuAcqRepetitionTime",  # ????
    "InversionTime": "VisuAcqInversionTime",
    "SliceEncodingDirection": [
        {"key": "VisuAcqGradEncoding", "where": "slice_enc"},
        {"EncSeq": "VisuAcqGradEncoding", "Equation": "len(EncSeq)"},
    ],
    "SliceTiming": {
        "Equation": "np.linspace(0, TR/1000, Num_of_Slice + 1)[Order]",
        "Num_of_Slice": "VisuCoreFrameCount",
        "Order": "ACQ_obj_order",
        "TR": "VisuAcqRepetitionTime",
    },
    #### "RFandContrast" ####
    "FlipAngle": "VisuAcqFlipAngle",
    ##### "EPIandB0mapping" ####
    #### "Others" ####
    # "CoilConfigName": "ACQ_coil_config_file",
}


metadata_ref_DICOM_MRS = {
    #### "Subject" ####
    "Date": "AcquisitionDate", # 0008,0022
    "Time": "AcquisitionTime", # 0008,0032
    "UserName": "StudyDescription", # 0008,1030
    "SubjectID": "PatientName", # 0010,0010
    "SessionID": "AccessionNumber", # 0008,0050
    # "SubjectEntry"
    # "SubjectPos"
    # "SubjectType": [0x0010,0x2210], # 0010,2210
    #### "HardwareInformation" ####
    "Modality": "Modality", # 0008,0060
    "Manufacturer": "Manufacturer", # 0008,0070
    "ManufacturersModelName": "ManufacturerModelName", # 0008,1090
    "DeviceSerialNumber": "DeviceSerialNumber", # 0018,1000
    "StationName": "StationName", # 0008,1010
    "SoftwareVersion": "SoftwareVersion", # 0018,1020
    "MagneticFieldStrength": "MagneticFieldStrength", # 0018,0087
    # "ImagingFrequency": "ImagingFrecuency" # 0018,0084
    #### "InstitutionInformation" ####
    "InstitutionName": "InstitutionName", # 0008,0080
    #### "SequenceSpecifics" ####
    "PulseSequenceDetails": "ProtocolName", # 0018,1030
    "PulseSequenceType": "SeriesDescription", # 0008,103E
    "SequenceName": "SequenceName", # 0018,0024
    # "ScanOptions": {
    #     "CG": "VisuCardiacSynchUsed",
    #     "FC": "VisuAcqFlowCompensation",
    #     "FP": "VisuAcqSpectralSuppression",
    #     "PFF": {"idx": 0, "key": "VisuAcqPartialFourier"},
    #     "PFP": {"idx": 1, "key": "VisuAcqPartialFourier"},
    #     "RG": "VisuRespSynchUsed",
    #     "SP": "PVM_FovSatOnOff",
    # },
    #### "SpatialEncoding" ####
    # "EffectiveEchoSpacing": {
    #     "ACCfactor": "ACQ_phase_factor",
    #     "BWhzPixel": "VisuAcqPixelBandwidth",
    #     "Equation": "(1 / (MatSizePE * BWhzPixel)) / " "ACCfactor",
    #     "MatSizePE": {
    #         "idx": [
    #             {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
    #             {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
    #         ],
    #         "key": "VisuCoreSize",
    #     },
    # },
    # "NumberShots": "VisuAcqKSpaceTrajectoryCnt",
    # "ParallelReductionFactorInPlane": "ACQ_phase_factor",
    # "PartialFourier": "VisuAcqPartialFourier",
    # "PhaseEncodingDirection": [
    #     {"key": "VisuAcqGradEncoding", "where": "phase_enc"},
    #     {"key": "VisuAcqImagePhaseEncDir", "where": "col_dir"},
    # ],
    # "TotalReadoutTime": {
    #     "ACCfactor": "ACQ_phase_factor",
    #     "BWhzPixel": "VisuAcqPixelBandwidth",
    #     "ETL": "VisuAcqEchoTrainLength",
    #     "Equation": "(1 / BWhzPixel) / ACCfactor",
    # },
    #### "TimingParameters" ####
    # "DwellTime": {"BWhzPixel": "VisuAcqPixelBandwidth", "Equation": "1/BWhzPixel"},
    "EchoTime": "EchoTime", # 0018,0081
    "RepetitionTime": "RepetitionTime", # 0018,0080
    "InversionTime": "InversionTime", # 0018,0082
    # "SliceEncodingDirection": [
    #     {"key": "VisuAcqGradEncoding", "where": "slice_enc"},
    #     {"EncSeq": "VisuAcqGradEncoding", "Equation": "len(EncSeq)"},
    # ],
    # "SliceTiming": {
    #     "Equation": "np.linspace(0, TR/1000, Num_of_Slice + 1)[Order]",
    #     "Num_of_Slice": "VisuCoreFrameCount",
    #     "Order": "ACQ_obj_order",
    #     "TR": "VisuAcqRepetitionTime",
    # },
    #### "RFandContrast" ####
    "FlipAngle": "FlipAngle", # 0018,1314
    #### "EPIandB0mapping" ####
    #### "Others" ####
    "NumberOfAverages": "NumberOfAverages", # 0018,0083
}

auto_processing_options = {
    # b: Bruker, m: MRsolutions, c: Resomapper
    "input_format": "b",

    # ["T1 map", "T2 map", "T2star map", "MTR map", "DTI"]
    "modals_to_process": ["T1 map", "T2 map", "T2star map", "MTR map", "DTI"],
    
    "T1 map": {
        "denoising": False,
    },
    "T2 map":{
        "denoising": False,
    },
    "T2star map":{
        "denoising": False,
    },
    "MTR map":{
        "denoising": True,
        # n, d, a, p, l, m
        "denoising_filter": "a",
        "denoising_params": "default",
    },
    "DTI":{
        "denoising": True,
        "denoising_filter": "p",
        "denoising_params": "default",
    }
}


class NotStudiesToConvertError(ValueError):
    def __init__(self, *args):
        super(NotStudiesToConvertError, self).__init__(
            "There are no studies to convert.", *args
        )


class NoModalsSelectedError(ValueError):
    def __init__(self, *args):
        super(NoModalsSelectedError, self).__init__(
            "You haven't selected any modalities to process.", *args
        )


class NotStudiesToProcessError(ValueError):
    def __init__(self, *args):
        super(NotStudiesToProcessError, self).__init__(
            "There are no studies to process.", *args
        )