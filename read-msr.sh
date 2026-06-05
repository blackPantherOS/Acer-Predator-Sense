#!/bin/bash

# Ellenőrizze, hogy a felhasználó root-e
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Load msr module if not already loaded
if ! lsmod | grep -q msr; then
    modprobe msr
fi

# Function to read MSR and convert to human-readable format
read_msr() {
    local register=$1
    local bitfield=$2
    local scale=$3
    local result

    result=$(rdmsr -f $bitfield -d $register 2>&1)
    if [[ $? -ne 0 ]]; then
        echo "Failed to read MSR $register: $result"
        return 1
    fi

    echo $(awk -v value=$result -v scale=$scale 'BEGIN {printf "%.2f", value * scale}')
}

# Read temperature target (adjust -8)
temperature_target_raw=$(rdmsr -f 23:16 -d 0x1a2 2>&1)
if [[ $? -ne 0 ]]; then
    echo "Failed to read temperature target: $temperature_target_raw"
else
    temperature_target=$((temperature_target_raw - 8))
fi

# Read voltage values
core_voltage=$(read_msr 0x150 32:47 0.001)
gpu_voltage=$(read_msr 0x150 48:63 0.001)
cache_voltage=$(read_msr 0x150 16:31 0.001)
uncore_voltage=$(read_msr 0x150 0:15 0.001)
analogio_voltage=$(read_msr 0x150 64:79 0.001)

# Read power limits (example values, need to verify MSR documentation for exact bitfields)
short_power_limit=$(read_msr 0x610 32:46 0.125)
long_power_limit=$(read_msr 0x610 0:14 0.125)
short_time_window=$(read_msr 0x610 49:63 0.0000001)
long_time_window=$(read_msr 0x610 17:23 0.0000001)

# Check turbo status
turbo_status=$(rdmsr -f 38:38 -d 0x1a0 2>&1)
if [[ $? -ne 0 ]]; then
    echo "Failed to read turbo status: $turbo_status"
else
    if [ "$turbo_status" -eq 0 ]; then
        turbo="disable"
    else
        turbo="enable"
    fi
fi

# Print results
echo "temperature target: ${temperature_target}C"
echo "core: ${core_voltage} mV"
echo "gpu: ${gpu_voltage} mV"
echo "cache: ${cache_voltage} mV"
echo "uncore: ${uncore_voltage} mV"
echo "analogio: ${analogio_voltage} mV"
echo "powerlimit: ${short_power_limit}W (short: ${short_time_window}s - disabled) / ${long_power_limit}W (long: ${long_time_window}s - enabled)"
echo "turbo: ${turbo}"

