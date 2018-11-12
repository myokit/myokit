#
# Powershell script for OpenCL Installation on Appveyor
#
# Adapted from: https://github.com/tunnelvisionlabs/NOpenCL
#

# Download Intel OpenCL SDK (unless already present), and install
If (-not (Test-Path 'intel_sdk.exe')) {
	Invoke-WebRequest http://registrationcenter-download.intel.com/akdlm/irc_nas/vcp/12527/intel_sdk_for_opencl_2017_7.0.0.2567.exe -OutFile intel_sdk.exe
}
.\intel_sdk.exe install --output=C:\output.log --eula=accept | Out-Null

# Download Intel OpenCL runtime (unless already present)
If (-not (Test-Path 'opencl_runtime.msi')) {
	#Invoke-WebRequest http://registrationcenter-download.intel.com/akdlm/irc_nas/9022/opencl_runtime_16.1.1_x64_setup.msi -OutFile opencl_runtime.msi
	Invoke-WebRequest http://registrationcenter-download.intel.com/akdlm/irc_nas/vcp/13794/opencl_runtime_18.1_x64_setup.msi -OutFile opencl_runtime.msi
}
#msiexec.exe /i opencl_runtime.msi /qn | Out-Null
