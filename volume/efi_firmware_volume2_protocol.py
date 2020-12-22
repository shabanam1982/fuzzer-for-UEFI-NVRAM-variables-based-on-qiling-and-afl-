from qiling.os.uefi.const import EFI_UNSUPPORTED
from .efi_firmware_volume2_type import EFI_FIRMWARE_VOLUME2_PROTOCOL
import ctypes
from qiling.os.uefi.fncc import *
from qiling.os.const import *
import uefi_firmware
from enum import Enum

class EFI_SECTION_TYPE(Enum):
    PE32                  = 0x10
    PIC                   = 0x11
    TE                    = 0x12
    DXE_DEPEX             = 0x13
    VERSION               = 0x14
    USER_INTERFACE        = 0x15
    COMPATIBILITY16       = 0x16
    FIRMWARE_VOLUME_IMAGE = 0x17
    FREEFORM_SUBTYPE_GUID = 0x18
    RAW                   = 0x19
    PEI_DEPEX             = 0x1B
    SMM_DEPEX             = 0x1C

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "FvAttributes": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
})
def hook_GetVolumeAttributes(ql, address, params):
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "FvAttributes": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
})
def hook_SetVolumeAttributes(ql, address, params):
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "NameGuid": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "Buffer": POINTER,
    "BufferSize": POINTER,
    "FoundType": POINTER,
    "FileAttributes": POINTER,
    "AuthenticationStatus": POINTER,
})
def hook_ReadFile(ql, address, params):
    return EFI_UNSUPPORTED

def get_file(ql, guid):
    for volume in ql.os.firmware_volumes:
        objects = volume.iterate_objects(False)
        print(objects)
        # for fs in volume.firmware_filesystems:
        #     for file in fs.files:
        #         if file.type == 0x0b: # EFI_FV_FILETYPE_FIRMWARE_VOLUME_IMAGE
        #             pass
        #         else:


@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "NameGuid": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "SectionType": INT,
    "SectionInstance": INT,
    "Buffer": POINTER,
    "BufferSize": POINTER,
    "AuthenticationStatus": POINTER,
})
def hook_ReadSection(ql, address, params):
    # import ipdb; ipdb.set_trace()
    guid = str(ql.os.read_guid(params["NameGuid"]))
    section_type = params["SectionType"] & 0xFF
    # print(guid)
    # import ipdb; ipdb.set_trace()   
    for volume in ql.os.firmware_volumes:
        objects = uefi_firmware.utils.flatten_firmware_objects(volume.iterate_objects())
        # print(len(objects))
        # import ipdb; ipdb.set_trace()
        for obj in objects:
            if obj['guid'] == guid:
                counter = -1
                for section in obj['_self'].sections:
                    if section.type == section_type:
                        counter += 1
                        if counter == params["SectionInstance"]:
                            print(section.data)
                            import ipdb; ipdb.set_trace()
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "NumberOfFiles": INT, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "WritePolicy": INT,
    "FileData": POINTER,
})
def hook_WriteFile(ql, address, params):
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "Key": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "FileType": POINTER,
    "NameGuid": POINTER,
    "Attributes": POINTER,
    "Size": POINTER,
})
def hook_GetNextFile(ql, address, params):
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "InformationType": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "BufferSize": POINTER,
    "Buffer": POINTER,
})
def hook_GetInfo(ql, address, params):
    return EFI_UNSUPPORTED

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SW_DISPATCH2_PROTOCOL)
    "InformationType": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "BufferSize": INT,
    "Buffer": POINTER,
})
def hook_SetInfo(ql, address, params):
    return EFI_UNSUPPORTED

def install_EFI_FIRMWARE_VOLUME2_PROTOCOL(ql, start_ptr):
    efi_firmware_volume2_protocol = EFI_FIRMWARE_VOLUME2_PROTOCOL()
    ptr = start_ptr + ctypes.sizeof(EFI_FIRMWARE_VOLUME2_PROTOCOL)
    pointer_size = 8

    efi_firmware_volume2_protocol.GetVolumeAttributes = ptr
    ql.hook_address(hook_GetVolumeAttributes, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.SetVolumeAttributes = ptr
    ql.hook_address(hook_SetVolumeAttributes, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.ReadFile = ptr
    ql.hook_address(hook_ReadFile, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.ReadSection = ptr
    ql.hook_address(hook_ReadSection, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.WriteFile = ptr
    ql.hook_address(hook_WriteFile, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.GetNextFilen = ptr
    ql.hook_address(hook_GetNextFile, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.GetInfo = ptr
    ql.hook_address(hook_GetInfo, ptr)
    ptr += pointer_size

    efi_firmware_volume2_protocol.SetInfo = ptr
    ql.hook_address(hook_SetInfo, ptr)
    ptr += pointer_size

    return (ptr, efi_firmware_volume2_protocol)
