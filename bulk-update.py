# To use this bulk update script setup your OCI config file, locate tag_update value, add details to update to instances, run program

# For swift of use this can quickly be deployed from the OCI Cloud Shell by Git cloning this script and setting up a Python environment

import oci

# Determines the list of subscribed regions for the tenancy
def load_list_of_regions(tenancy_id, identity_client):

    print('Loading regions...')
    list_of_regions = []
    list_regions_response = identity_client.list_region_subscriptions(tenancy_id)
    for r in list_regions_response.data:
        list_of_regions.append(r.region_name)
        print('    Subscribed to:', r.region_name)


    return list_of_regions

# Updates all compute instance(s) details in all compartments for a region
def update_all_compute_resources_in_region(regions, config, compartments):

    compute = oci.core.ComputeClient(config)

    # Define update details for instance
    tag_update = oci.core.models.UpdateInstanceDetails(freeform_tags={'test': '7'}, defined_tags={'Yeetum_IT' :{'Workload':'atlas-mta', 'Contact':'tobalo.torres@oracle.com'}})

    for region in regions:

        print('Looking thorough region:', region)
        instances = []
        instance_total = 0
        try:
            for compartment in compartments:
                print('    Looking through compartment:', compartment.name)
                instances = oci.pagination.list_call_get_all_results(compute.list_instances,compartment.id,sort_by="DISPLAYNAME").data
                
                for instance in instances:
                    print('        Updating instance:', instance.display_name)
                    instance_total += 1
                    updated_instance = compute.update_instance(instance.id, tag_update).data
                    print('            Updated freeform tags to:', updated_instance.freeform_tags)
                    print('            Updated defined tags to:', updated_instance.defined_tags)



        except Exception as e:
            raise RuntimeError("Error in update_all_compute_resources_in_region: " + str(e.args))
        finally:
            print('Updated', str(instance_total), 'instance(s) in:', region)

def identity_read_compartments(identity, tenancy):

    print("Loading Compartments...")

    try:
        compartments = oci.pagination.list_call_get_all_results(
            identity.list_compartments,
            tenancy.id,
            compartment_id_in_subtree=True
        ).data

        # Add root compartment which is not part of the list_compartments
        compartments.append(tenancy)


        print("    Total " + str(len(compartments)) + " compartments loaded.")
        return compartments

    except Exception as e:
        raise RuntimeError("Error in identity_read_compartments: " + str(e.args))



if __name__ == "__main__":
    
    # Main code
    config = oci.config.from_file()
    identity = oci.identity.IdentityClient(config)
    tenancy = identity.get_tenancy(config["tenancy"]).data

    regions = load_list_of_regions(tenancy.id, identity)
    compartments = identity_read_compartments(identity, tenancy)
    update_all_compute_resources_in_region(regions,config,compartments)

    