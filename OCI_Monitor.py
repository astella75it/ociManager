#!/usr/local/bin/python3

# author: Oracle
# 2021.04.10 alessandro.stella@oracle.com first draft version
# 2022.09.02 alessandro.stella@oracle.com added configuration file and section as parameters
# 2024.02.11 alessandro.stella@oracle.com add compute option to print compute vm for every compartment
#

import os
import json
import oci
import getopt
import sys
import argparse
from terminaltables import AsciiTable
#oci packages

#######################################################################################
def debugPrint(p_debug, p_string):
#######################################################################################
   if p_debug >= 30:
      print(p_string)

#######################################################################################
def OCI_Config(p_config_file, p_config_section):
#######################################################################################

   #setting config path, default path is ~/.oci/config (make sure not on VPN)
   #oci_config = oci.config.from_file("~/.oci/config", p_configuration_section)
   oci_config = oci.config.from_file(p_config_file, p_config_section)

   #validating configuration file, making sure the connection is established
   oci.config.validate_config(oci_config)

   return oci_config

#######################################################################################
def OCI_Identity(p_config):
#######################################################################################

   #setting and initializing OCI parameters
   oci_identity = oci.identity.IdentityClient(p_config)

   return oci_identity

#######################################################################################
def OCI_GetTagToSet(p_config):
#######################################################################################

   oci_update_instance_details=oci.core.models.UpdateInstanceDetails ()
   oci_update_instance_details.defined_tags={"COSTO": {"cost_center": "se_italy"}, "Schedule": {"AnyDay": "0,0,0,0,0,0,0,*,*,*,*,*,*,*,*,*,*,*,*,0,0,0,0,0"}}

   return oci_update_instance_details

#######################################################################################
def printUserInformation(p_config, p_user):
#######################################################################################

   os.system('clear')
   print("***************************************************************************************************************")
   print("\nUSER => " + p_config["user"])
   print("\n\t " + p_user.name)
   print("\t " + p_user.lifecycle_state)
   print("***************************************************************************************************************")

#######################################################################################
def _deprecated_printComputeInstancesInCompartment(p_compute_instance_table_metadata):
#######################################################################################
  table_data = [[ "Display Name", "Lifecycle Status", "Public IPs", "Oracle Cloud ID"]]

  for row in p_compute_instance_table_metadata:
      table_data.append([row["display_name"], row["lifecycle_state"], ", ".join(row["public_ips"]), row["id"]])

  print(AsciiTable(table_data).table)

#######################################################################################
def getLBsInCompartment(p_config, p_tenant, p_compartment_id):
#######################################################################################
  v_lb_client=oci.load_balancer.LoadBalancerClient(p_config)
  v_lb_list=v_lb_client.list_load_balancers(p_compartment_id).data
  ##print("*** getLBsInCompartment ***")
  ##print(v_lb_list)

  #for lb in v_lb_list:
  ##
  ## this dict stores the relevant instance details
  ##
#    instance_info = {"display_name": vm.display_name,
#                     "id": vm.id,
#                     "lifecycle_state": vm.lifecycle_state,
#                     "public_ips": [ ]
#                    }

#    if vm.lifecycle_state == "TERMINATED":
#      continue

#    all_instance_metadata.append(instance_info)

  #return all_instance_metadata
  return v_lb_list



#######################################################################################
def getComputeInstancesInCompartment(p_config, p_tenant, p_compartment_id):
#######################################################################################
  all_instance_metadata = [];
  v_compute_client=oci.core.ComputeClient(p_config)
  v_compute_list=v_compute_client.list_instances(p_compartment_id).data
  for vm in v_compute_list:
  #
  # this dict stores the relevant instance details
  #
    instance_info = {"display_name": vm.display_name,
                     "id": vm.id,
                     "lifecycle_state": vm.lifecycle_state,
                     "public_ips": [ ]
                    }

    if vm.lifecycle_state == "TERMINATED":
      continue

    all_instance_metadata.append(instance_info)

  #return all_instance_metadata
  return v_compute_list

#######################################################################################
def printTenantInformation(p_config, p_tenant):
#######################################################################################

   print("\nTENANT => " + p_config["tenancy"])
   print("\n\t " + p_tenant.name)
   print("***************************************************************************************************************")

#######################################################################################
def printLBStatus(p_lb_list, p_compartment_level, p_print):
#######################################################################################
  if p_print:
    v_indent = "\t"
    v_indentation = v_indent*p_compartment_level
    if len(p_lb_list) > 0:
       print("\n" + v_indentation + " LOAD BALANCER")
       print(v_indentation + "---------------------------------------------------------------------------------------------------------------------------------------")
       for j in range(len(p_lb_list)):
         print(v_indentation + " | " + p_lb_list[j].display_name[:40].ljust(50)
                            ## + " | " + p_lb_list[j].ip_addresses[]
                             + " | " + p_lb_list[j].lifecycle_state.ljust(20)
                             + " | " + p_lb_list[j].shape_name.ljust(30)+ " | "
              )
         print(v_indentation + "---------------------------------------------------------------------------------------------------------------------------------------" + "\n")


#######################################################################################
def printComputeStatus(p_instances_list, p_compartment_level, p_print):
#######################################################################################
  if p_print:
    v_indent = "\t"
    v_indentation = v_indent*p_compartment_level
    if len(p_instances_list) > 0:
       print("\n" + v_indentation + " COMPUTE")
       print(v_indentation + "---------------------------------------------------------------------------------------------------------------------------------------")
       for j in range(len(p_instances_list)):
         print(v_indentation + " | " + p_instances_list[j].display_name[:40].ljust(50)
                             + " | " + p_instances_list[j].availability_domain.ljust(20)
                             + " | " + p_instances_list[j].lifecycle_state.ljust(20)
                             + " | " + p_instances_list[j].shape.ljust(30)+ " | "
              )
       print(v_indentation + "---------------------------------------------------------------------------------------------------------------------------------------" + "\n")

#######################################################################################
def printAnalyticStatus(p_analytics_list):
#######################################################################################
   if len(p_analytics_list) > 0:
      print("\n ANALYTICS")
      print("\n\t /---------------------------------------------------------------------------------------------------------------------------------------\ ")
      for j in range(len(p_analytics_list)):
         print("\t | " + p_analytics_list[j].name[:28].ljust(30)
               + " | " + p_analytics_list[j].service_url[:48].ljust(50)
               + " | " + p_analytics_list[j].lifecycle_state.ljust(20)
              + " | " + p_analytics_list[j].feature_set.ljust(25)+ " | ")
      print("\t \---------------------------------------------------------------------------------------------------------------------------------------/")

#######################################################################################
def printAutonomousStatus(p_adb_list):
#######################################################################################
   if len(p_adb_list) > 0:
      print("\n AUTONOMOUS")
      print("\n\t /---------------------------------------------------------------------------------------------------------------------------------------\ ")
      for j in range(len(p_adb_list)):
         print("\t | " + p_adb_list[j].db_name[:15].ljust(15)
               + " | " + p_adb_list[j].db_workload[:5].ljust(5)
               + " | " + p_adb_list[j].db_version.ljust(20)
               + " | " + str(p_adb_list[j].cpu_core_count).ljust(5)
               + " | " + str(p_adb_list[j].data_storage_size_in_tbs).ljust(5)
               + " | " + p_adb_list[j].lifecycle_state[:20].ljust(20) + " | " )
      print("\t \---------------------------------------------------------------------------------------------------------------------------------------/")

#######################################################################################
def printDBsystemStatus(p_dbs_list, p_database_client, p_compartment_ocid):
#######################################################################################
   if len(p_dbs_list) > 0:
      print("\n DBSYSTEM")
      print("\n\t /---------------------------------------------------------------------------------------------------------------------------------------\ ")
      for j in range(len(p_dbs_list)):
         print("\t | " + p_dbs_list[j].display_name[:15].ljust(15)
               + " | " + p_dbs_list[j].license_model[:20].ljust(5)
               + " | " + p_dbs_list[j].database_edition.ljust(20)
               + " | " + str(p_dbs_list[j].cpu_core_count).ljust(5)+ " | "
               + str(p_dbs_list[j].data_storage_size_in_gbs).ljust(5) + " | "
               + p_dbs_list[j].shape[:20].ljust(20) + " | " )
         db_nodes = p_database_client.list_db_nodes(compartment_id=p_compartment_ocid,db_system_id=p_dbs_list[j].id).data
         for k in range(len(db_nodes)):
            print("\t\t " + db_nodes[k].hostname.ljust(15)
                 + " | " + db_nodes[k].lifecycle_state.ljust(20)
                 )
      print("\t \---------------------------------------------------------------------------------------------------------------------------------------/")

#######################################################################################
def setDBsystemTag(p_dbs_list, p_database_client, p_config):
#######################################################################################
   if len(p_dbs_list) > 0:
      print("\n Setting Scheduling Tag on DBsystem")
      for j in range(len(p_dbs_list)):
         print("\t updating " + p_dbs_list[j].display_name, end = '')
         p_database_client.update_db_system(dbs_list[j].id, OCI_GetTagToSet(p_config))
         print("..done")

#######################################################################################
def setAutonomousTag(p_adb_list, p_adb_client, p_config):
#######################################################################################
   if len(p_adb_list) > 0:
      print("\n Setting Scheduling Tag on Autonomous")
      for j in range(len(p_adb_list)):
         print("\t updating " + p_adb_list[j].display_name, end = '')
         p_adb_client.update_autonomous_database(p_adb_list[j].id, OCI_GetTagToSet(p_config))
         print("..done")

#######################################################################################
def setAnalyticsTag(p_analytics_list, p_analytics_client, p_config):
#######################################################################################
   if len(p_analytics_list) > 0:
      print("\n Setting Scheduling Tag on Analytics")
      for j in range(len(p_analytics_list)):
         #print(p_analytics_list[j])
         #print("\t updating " + p_analytics_list[j].description, end = '')
         p_analytics_client.update_analytics_instance(p_analytics_list[j].id, OCI_GetTagToSet(p_config))
         print("..done")

#######################################################################################
def setComputeTag(p_instances_list, p_compute_client,p_config):
#######################################################################################
   if len(p_instances_list) > 0:
      print("\n Setting Scheduling Tag on Compute")
      for j in range(len(p_instances_list)):
         if p_instances_list[j].display_name != 'seldonml' and  p_instances_list[j].display_name != 'Schedule' and  p_instances_list[j].display_name != 'ATP' and  p_instances_list[j].display_name != 'OBIA_TEST' :
            print("\t updating " + p_instances_list[j].display_name, end = '')
            p_compute_client.update_instance(p_instances_list[j].id, OCI_GetTagToSet(p_config))
            print("..done")

#######################################################################################
def ReadChildCompartments(p_compartment,p_login):
#######################################################################################
    compartmentlist=oci.pagination.list_call_get_all_results(p_login.list_compartments,compartment_id=p_compartment,
                               access_level="ANY",compartment_id_in_subtree=False,lifecycle_state="ACTIVE",
                               sort_by="TIMECREATED",sort_order="DESC"
                               )
    compartmentlist.data.append(p_login.get_compartment(p_compartment).data)
    return compartmentlist.data

#######################################################################################
def ReadCompartments(p_tenancy,p_login):
#######################################################################################
    compartmentlist=oci.pagination.list_call_get_all_results(p_login.list_compartments,p_tenancy,
                               access_level="ANY",compartment_id_in_subtree=False,lifecycle_state="ACTIVE",
                               sort_by="TIMECREATED",sort_order="DESC"
                               )
    compartmentlist.data.append(p_login.get_compartment(p_tenancy).data)
    return compartmentlist.data

#######################################################################################

#######################################################################################
def ReadAllCompartments(p_tenancy,p_login):
#######################################################################################
    compartmentlist=oci.pagination.list_call_get_all_results(p_login.list_compartments,p_tenancy,
                               access_level="ANY",compartment_id_in_subtree=True,lifecycle_state="ACTIVE"
                               )
    compartmentlist.data.append(p_login.get_compartment(p_tenancy).data)
    return compartmentlist.data

#######################################################################################
def readAllUsers(p_tenancy,p_login):
#######################################################################################
    userlist=oci.pagination.list_call_get_all_results(p_login.list_users,p_tenancy, sort_by="NAME", lifecycle_state="ACTIVE")
    #userlist.data.append(p_login.get_user(p_tenancy).data)
    #return userlist.data

#######################################################################################
def printCompartmentList(p_config, p_identityClient, p_service):
#######################################################################################
  v_print_compute=False
  v_print_lb=False

  l1_compartment_list = ReadChildCompartments(p_config['tenancy'],p_identityClient)
  l1_compartments=len(l1_compartment_list)

  print("Service: " + p_service)
  print(l1_compartments)
  print("\nCOMPARTMENS LIST  ")

  if (p_service == "Compute"):
    v_print_compute=True
  elif (p_service == "LB"):
    v_print_lb=True


  for i in range(l1_compartments):
    if (l1_compartment_list[i].name == tenantResponse.name):
      l2_compartment_list = ReadChildCompartments(l1_compartment_list[i].id,p_identityClient)
      l2_compartments=len(l2_compartment_list)
      print(str(i) + " - " +  l1_compartment_list[i].name + " [" + str(l2_compartments) + "]") ## + "\n\tID: " + l1_compartment_list[i].id)
      ####
      ####
      printComputeStatus(getComputeInstancesInCompartment(p_config, p_identityClient, l1_compartment_list[i].id), 1, v_print_compute)
      ##printLBStatus(getLBsInCompartment(p_config, p_identityClient, l1_compartment_list[i].id), 2, v_print_lb)
      printLBStatus(getLBsInCompartment(p_config, p_identityClient, l1_compartment_list[i].id), 1, v_print_lb)
      ####
      ####
      for j in range(l2_compartments):
        if (l2_compartment_list[j].name != tenantResponse.name):
          l3_compartment_list = ReadChildCompartments(l2_compartment_list[j].id,p_identityClient)
          #################################################################################################################
          ### nella l3_compartment_list, la lista dei compartment prevede sempre come ultimo elemento il compartment padre.
          ### per questa ragione togliamo un elemento dalla len per ciclare solo sui compartment figlio nel for successivo
          ### questo vale per tutti i livelli.
          #################################################################################################################
          l3_compartments=len(l3_compartment_list)-1
          print("\t|---" + str(j) + " - " +  l2_compartment_list[j].name + " [" + str(l3_compartments) + "]") ## + "\n\t\tID: " + l2_compartment_list[j].id)
          ####
          printComputeStatus(getComputeInstancesInCompartment(p_config, p_identityClient, l2_compartment_list[j].id), 2, v_print_compute)
          printLBStatus(getLBsInCompartment(p_config, p_identityClient, l2_compartment_list[j].id), 2, v_print_lb)
          ####
          for k in range(l3_compartments):
            l4_compartment_list = ReadChildCompartments(l3_compartment_list[k].id,p_identityClient)
            l4_compartments=len(l4_compartment_list)-1
            print("\t\t|---" + str(k) + " - " +  l3_compartment_list[k].name + " [" + str(l4_compartments) + "]") ## + "\ni\t\t\tID: " + l3_compartment_list[k].id)
            ####
            printComputeStatus(getComputeInstancesInCompartment(p_config, p_identityClient, l3_compartment_list[k].id), 3, v_print_compute)
            ####
            for x in range(l4_compartments):
              l5_compartment_list = ReadChildCompartments(l4_compartment_list[x].id,p_identityClient)
              l5_compartments=len(l5_compartment_list)-1
              print("\t\t\t|---" + str(x) + " - " +  l4_compartment_list[x].name + " [" + str(l5_compartments) + "]")
              for z in range(l5_compartments):
                l6_compartment_list = ReadChildCompartments(l5_compartment_list[z].id,p_identityClient)
                l6_compartments=len(l6_compartment_list)-1
                print("\t\t\t\t|---" + str(z) + " - " +  l5_compartment_list[z].name + " [" + str(l6_compartments) + "]")
                for y in range(l6_compartments):
                  l7_compartment_list = ReadChildCompartments(l6_compartment_list[y].id,p_identityClient)
                  l7_compartments=len(l7_compartment_list)-1
                  print("\t\t\t\t\t|---" + str(y) + " - " +  l6_compartment_list[y].name + " [" + str(l7_compartments) + "]")


#######################################################################################
# M A I N
#######################################################################################
argv=sys.argv[1:]
configuration_section=""
configuration_file=""
target_compartments=""
check_operation=""
set_operation=""
service_name=""
p_debug_level=0

opts, args = getopt.getopt(argv,"hc:f:d:t:k:u:s:o")

for opt, arg in opts:
   if opt in ['-h']:
      print("usage: ./OCI-Monitor -h |-f <Configuration file> | -t <Configuration Section> | -k [getCompartments|getComputes|getLBs||getUsers|getUsersPolicies] | -c <single compartment name>|ALL | -d <debug level> | -o <output format>")
      sys.exit(2)
   elif opt in ['-k']:
      check_operation = arg
   elif opt in ['-s']:
      service_name = arg
   elif opt in ['-c']:
      target_compartments = arg
   elif opt in ['-f']:
      configuration_file = arg
   elif opt in ['-d']:
      p_debug_level = int(arg)
   elif opt in ['-t']:
      configuration_section = arg
   elif opt in ['-o']:
      output_format = arg
   else:
      assert False, "unhandled option"

configDict = OCI_Config(configuration_file, configuration_section)
identityClient = OCI_Identity(configDict)
userResponse = identityClient.get_user(configDict["user"]).data
debugPrint(p_debug_level, "*** User Response ***")
debugPrint(p_debug_level, userResponse)
tenantResponse = identityClient.get_tenancy(configDict["tenancy"]).data
debugPrint(p_debug_level, "*** Tenant Response ***")
debugPrint(p_debug_level, tenantResponse)

printUserInformation(configDict, userResponse)
printTenantInformation(configDict, tenantResponse)
print (configuration_file, configuration_section, check_operation, set_operation, target_compartments, service_name)


if (check_operation=="getCompartments"):
  p_service='Compartment'
  printCompartmentList(configDict, identityClient, p_service)
elif (check_operation=="getUsers"):
  print(check_operation)
  list_users_response=identityClient.list_users(tenantResponse.id, sort_by="NAME",lifecycle_state="ACTIVE")
  print(list_users_response.data)
  print(list_users_response.data.description)
  #readAllUsers(tenantResponse.id,identityClient)
elif (check_operation=="getUsersPolicies"):
  print(check_operation)
elif (check_operation=="getComputes"):
  p_service='Compute'
  printCompartmentList(configDict, identityClient, p_service)
elif (check_operation=="getLBs"):
  p_service='LB'
  printCompartmentList(configDict, identityClient, p_service)

else:
  print("Operation non found")
  sys.exit(1)

###############
###############
###############

sys.exit(0)
user_list = ReadAllUsers(config['tenancy'],identity)
usersNum = len(user_list)
sys.exit(0)
