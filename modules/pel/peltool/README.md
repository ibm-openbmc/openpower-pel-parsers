# peltool Usage

To see all of peltool's capabilities, use the help option `peltool.py --help`.

**Note:** For non-BMC environment user must pass the PEL directory to parse PELs
          e.g. `peltool.py -p <pel_dir> -l`, `peltool.py -p <pel_dir> -n`,
               `peltool.py -p <pel_dir> -a`

## List PELs

- Get list of PELs: `peltool.py -l` (By default serviceable PELs are listed)
- Get list of PELs including non-serviceable PELs: `peltool.py -lN`
- Get list of PELs including hidden PELs: `peltool.py -lH`
- Get list of PELs including terminating PELs: `peltool.py -lt`
- Get list of serviceable, non-serviceable, and hidden PELs: `peltool.py -lsNH`

##### List PELs based on severity and only options

- Get list of serviceable PELs and PELs with another severity: `peltool.py -l -S <Severity>`
- Get list of PELS including PELs with severity as Informational: `peltool.py -l -S Informational`
  User can provide multiple severities values e.g. `peltool.py -l -S Informational Critical`
- Get list of PELs including hidden PELs only: `peltool.py -lHO`
- Get list of PELs including critical PELs only: `peltool.py -lO -S Critical`

## Show PEL Count

- Get PEL count: `peltool.py -n` (By default serviceable PELs count is given)
- Get PEL count including non-serviceable PELs: `peltool.py -nN`
- Get PEL count including hidden PELs: `peltool.py -nH`
- Get PEL count including terminating PELs: `peltool.py -nt`
- Get PEL count for serviceable, non-serviceable, and hidden PELs: `peltool.py -nsNH`

##### Show PEL count based on severity and only options

- Get count of serviceable PELs and PELs with another severity: `peltool.py -n -S <Severity>`
- Get PEL count including PELs with severity as Informational: `peltool.py -n -S Informational`
  User can provide multiple severities values e.g. `peltool.py -n -S Informational Critical`
- Get hidden PELs count only: `peltool.py -nHO`
- Get critical PELs count only: `peltool.py -nO -S Critical`

## Display all PEL data

- Get all PEL data: `peltool.py -a` (By default serviceable PELs data are displayed)
- Get all PEL data including hidden PELs: `peltool.py -aH`
- Get all PEL data including terminating PELs: `peltool.py -at`
- Get all PEL data for serviceable, non-serviceable, and hidden PELs: `peltool.py -asNH`

##### Get all PEL data based on severity and only options

- Get all data for serviceable PELs and PELs with another severity: `peltool.py -a -S <Severity>`
- Get all PEL data including PELs with severity as Informational: `peltool.py -a -S Informational`
  User can provide multiple severities values e.g. `peltool.py -l -S Informational Critical`
- Get hidden PELs data only: `peltool.py -aHO`
- Get critical PELs data only: `peltool.py -aO -S Critical`

## Delete PELs

- Delete single PEL: `peltool.py -d <Entry_ID>`
- Delete all PELs: `peltool.py -D`

## Get PELs based on ID type

- Get PEL data based entry ID: `peltool.py -i <Entry_ID>`
- Get PEL data based on BMC event log ID: `peltool.py —-bmc-id <BMC_Event_Log_ID>`
- Get PELs based on platform log ID: `peltool.py —-plid <Platform_Log_ID>`
- Get PELs based on System reference code: `peltool.py —-src <System_Reference_Code>`
  Note: This option can used to filter firmware, subsystem, component level PELs.
- Get PELs excluding the matched SRCs from the given file:  `peltool.py —-src-exclude <src_exclude_file>`

## Other peltool commands

- Store parsed PEL data in JSON format: `peltool.py -j -o <out_dir_path>`
- Delete the original file after parsing: `peltool.py -j -c`
- Get PEL data in hexadecimal format: `peltool.py -lx`
- Get PEL data from BMC PEL archive path: `peltool.py -lA`
- Get list of PELs in reverse order: `peltool.py -lr`
- Extract PEL data from specific file: `peltool.py  -f </path/to/pel/file>`
- Get PEL data from files with specific extension only: `peltool.py -l -e <extension_file_format>`
- Skip loading PEL parser plugins and list PELs: `peltool.py -lP`
