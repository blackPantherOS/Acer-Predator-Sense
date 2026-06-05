#!/bin/bash
rdmsr 0x198 -p 0 -u --bitfield 47:32
