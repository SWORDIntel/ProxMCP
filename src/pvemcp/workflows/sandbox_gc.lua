-- Ephemeral Sandbox Lifecycle
-- Cleanup routine for tmpl-* VMs
local templates = {"9000", "9100", "9101", "9102", "9103"}

for _, vmid in ipairs(templates) do
    local state = vm_state(vmid, "status")
    if state.ok and state.status == "running" then
        admin_notify("Stopping and reclaiming sandbox: " .. vmid, "Garbage Collection")
        vm_disk_reclaim(vmid)
        vm_state(vmid, "stop")
    else
        admin_notify("Sandbox " .. vmid .. " already stopped.", "Garbage Collection")
    end
end
return "Sandbox cleanup complete"
