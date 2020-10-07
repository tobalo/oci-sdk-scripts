config = {
    "user": 'INSERT_VALUE_HERE',
    "key_file": 'INSERT_VALUE_HERE',
    "fingerprint": 'INSERT_VALUE_HERE',
    "tenancy": 'INSERT_VALUE_HERE',
    "region": 'INSERT_VALUE_HERE'
}

from oci.config import validate_config
validate_config(config)