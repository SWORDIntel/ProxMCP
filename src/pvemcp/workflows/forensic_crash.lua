-- Forensic Crash Reporter
-- Triggered by pipeline failure events
local vmid = "9211"
local host = "192.168.1.252"
local log_path = "/tmp/pipeline_debug.log"

admin_notify("Pipeline failure detected on " .. vmid, "Forensic Path Initiated")

-- 1. Grab Log chunk
local log_res = remote_log_capture(host, log_path, 30)
if log_res.ok then
    admin_notify("Log captured successfully.", "Forensic Update")
else
    admin_notify("Failed to capture log.", "Forensic Error")
end

-- 2. Audit config
local diff_res = vm_etc_diff(vmid)
if diff_res.ok then
    admin_notify("Config diff completed.", "Forensic Update")
else
    admin_notify("Config diff failed.", "Forensic Error")
end

-- 3. Dump RAM
local dump_res = vm_ram_dump(vmid, "/tmp/crash_dump.bin")
if dump_res.ok then
    admin_notify("RAM dump captured.", "Forensic Update")
else
    admin_notify("Failed to capture RAM dump.", "Forensic Error")
end

return "Forensic package captured to /tmp/"
