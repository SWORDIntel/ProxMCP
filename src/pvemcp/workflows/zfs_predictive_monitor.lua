-- ZFS Predictive Health Monitor
-- Checks capacity and health, alerts if approaching threshold.

local pool = "tank"
local capacity_threshold = 85
local status = host_zfs_status(pool)

if not status.ok then
    admin_notify("Failed to query ZFS pool: " .. pool, "ZFS Guardian Error")
    return "Error querying pool"
end

-- Simple pattern match to find capacity in the output string
-- Output format for `zpool list -p tank`:
-- NAME SIZE ALLOC FREE CKPOINT EXPANDSZ FRAG CAP DEDUP HEALTH ALTROOT
-- tank ... ... ... ... ... ... 50% ... ONLINE -
local output = status.stdout
local cap_match = string.match(output, "(%d+)%%")
local health_match = string.match(output, "ONLINE")

if not health_match then
    admin_notify("ZFS Pool " .. pool .. " health issue detected!", "ZFS Guardian Alert")
    return "Health issue detected"
end

if cap_match then
    local cap = tonumber(cap_match)
    if cap >= capacity_threshold then
        admin_notify("ZFS Pool " .. pool .. " capacity at " .. cap .. "%. Action required.", "ZFS Guardian Alert")
        return "Capacity threshold exceeded: " .. cap .. "%"
    end
end

return "Pool " .. pool .. " healthy at " .. (cap_match or "unknown") .. "%"
EOF
