import oci
import sys
import argparse
import datetime
import json
import os

# Input compartment OCID
compartment_id = ''


##########################################################################
# Create signer for Authentication
# Input - config_profile and is_instance_principals and is_delegation_token
# Output - config and signer objects
##########################################################################
def create_signer(config_profile, is_instance_principals, is_delegation_token):

    # if instance principals authentications
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print_header("Error obtaining instance principals certificate, aborting")
            raise SystemExit

    # -----------------------------
    # Delegation Token
    # -----------------------------
    elif is_delegation_token:

        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print("*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                print("")
                raise SystemExit

            # check if file exist
            if not os.path.isfile(env_config_file):
                print("*** Config File " + env_config_file + " does not exist, Abort. ***")
                print("")
                raise SystemExit

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("* Key Error obtaining delegation_token_file")
            raise SystemExit

        except Exception:
            raise

    # -----------------------------
    # config file authentication
    # -----------------------------
    else:
        config = oci.config.from_file(
            oci.config.DEFAULT_LOCATION,
            (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
        )
        signer = oci.signer.Signer(
            tenancy=config["tenancy"],
            user=config["user"],
            fingerprint=config["fingerprint"],
            private_key_file_location=config.get("key_file"),
            pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
            private_key_content=config.get("key_content")
        )
        return config, signer

# Get Command Line Parser
parser = argparse.ArgumentParser()
parser.add_argument('-t', default="", dest='config_profile', help='Config file section to use (tenancy profile)')
parser.add_argument('-p', default="", dest='proxy', help='Set Proxy (i.e. www-proxy-server.com:80) ')
parser.add_argument('-ip', action='store_true', default=False, dest='is_instance_principals', help='Use Instance Principals for Authentication')
parser.add_argument('-dt', action='store_true', default=False, dest='is_delegation_token', help='Use Delegation Token for Authentication')
cmd = parser.parse_args()


config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)

def update_all_resources_in_compartment(compartment_id, config):

    compute = oci.core.ComputeClient(config)
    network = oci.core.VirtualNetworkClient(config)
    storage = oci.core.BlockstorageClient(config)

    # Define update details for instance
    compute_tag_update = oci.core.models.UpdateInstanceDetails(freeform_tags={'test': '7'}, defined_tags={})
    storage_tag_update = oci.core.models.UpdateBootVolumeDetails(freeform_tags={'test': '7'}, defined_tags={})
    network_tag_update = oci.core.models.UpdateVcnDetails(freeform_tags={'test': '7'}, defined_tags={})

    compute_resources = oci.pagination.list_call_get_all_results(compute.list_instances,compartment_id,sort_by="DISPLAYNAME").data
    network_resources = oci.pagination.list_call_get_all_results(network.list_virtual_circuits, compartment_id)
    storage_resources = oci.pagination.list_call_get_all_results(storage.list_volumes, compartment_id)
    

if __name__ == "__main__":
    
    # Main code
    try:
        print("\nConnecting to Identity Service...")
        identity = oci.identity.IdentityClient(config, signer=signer)
        if cmd.proxy:
            identity.base_client.session.proxies = {'https': cmd.proxy}

        tenancy = identity.get_tenancy(config["tenancy"]).data

        print("Tenant Name : " + str(tenancy.name))
        print("Tenant Id   : " + tenancy.id)
        print("")
        update_all_resources_in_compartment(compartment_id, config)


    except Exception as e:
        raise RuntimeError("\nError extracting compartments section - " + str(e))
