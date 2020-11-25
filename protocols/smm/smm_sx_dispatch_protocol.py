from .smm_sx_dispatch_type import EFI_SMM_SX_DISPATCH_PROTOCOL
from qiling.const import *
from qiling.os.const import *
from qiling.os.uefi.const import *
from .smm_sx_dispatch_type import *
from qiling.os.uefi.fncc import *
import ctypes

pointer_size = ctypes.sizeof(ctypes.c_void_p)

@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SX_DISPATCH2_PROTOCOL)
    "DispatchFunction": POINTER, #POINTER_T(ctypes.CFUNCTYPE(ctypes.c_uint64, POINTER_T(None), POINTER_T(None), POINTER_T(None), POINTER_T(ctypes.c_uint64)))
    "RegisterContext": POINTER, #POINTER_T(struct_EFI_SMM_SX_REGISTER_CONTEXT)
    "DispatchHandle": POINTER, #POINTER_T(POINTER_T(None))
})
def hook_SMM_SX_DISPATCH_Register(ql, address, params):
    return EFI_SUCCESS
    
@dxeapi(params={
    "This": POINTER, #POINTER_T(struct__EFI_SMM_SX_DISPATCH2_PROTOCOL)
    "DispatchHandle": POINTER, #POINTER_T(None)
})
def hook_SMM_SX_DISPATCH_UnRegister(ql, address, params):
    return EFI_UNSUPPORTED

def install_EFI_SMM_SX_DISPATCH_PROTOCOL(ql, start_ptr):
    efi_smm_sx_dispatch_protocol = EFI_SMM_SX_DISPATCH_PROTOCOL()
    ptr = start_ptr + ctypes.sizeof(EFI_SMM_SX_DISPATCH_PROTOCOL)
    pointer_size = 8

    efi_smm_sx_dispatch_protocol.Register = ptr
    ql.hook_address(hook_SMM_SX_DISPATCH_Register, ptr)
    ptr += pointer_size

    efi_smm_sx_dispatch_protocol.UnRegister = ptr
    ql.hook_address(hook_SMM_SX_DISPATCH_UnRegister, ptr)
    ptr += pointer_size

    return (ptr, efi_smm_sx_dispatch_protocol)

