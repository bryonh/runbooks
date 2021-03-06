#!/usr/bin/env python2
"""
    Installs a python package from a storage account so it can be used
    within an Azure automation account if the package is not available by default.
    You can upload the package to a storage account from your local system and then this
    runbook will download the package so it can be imported when the job is run.
"""
def install_packages(local_file_path, storage_account_name, storage_resource_group, storage_account_container_name):
    """
    Copies folders or files in a container from an Azure storage account to a local directory.

        Example 1:
                install_packages.py -p <local_file_path> -r <resource_group> -a <storage_account_name> -c <storage_account_container_name>

    Changelog:
        2017-09-11 AutomationTeam:
        -initial script

    """
    import os
    import base64
    import automationassets
    import azure.mgmt.storage
    from azure.storage.blob import BlockBlobService

    def get_automation_runas_credential(runas_connection):
        """ Returns credentials to authenticate against Azure resoruce manager """
        from OpenSSL import crypto
        from msrestazure import azure_active_directory
        import adal

        # Get the Azure Automation RunAs service principal certificate
        cert = automationassets.get_automation_certificate("AzureRunAsCertificate")
        pks12_cert = crypto.load_pkcs12(cert)
        pem_pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM, pks12_cert.get_privatekey())

        # Get run as connection information for the Azure Automation service principal
        application_id = runas_connection["ApplicationId"]
        thumbprint = runas_connection["CertificateThumbprint"]
        tenant_id = runas_connection["TenantId"]

        # Authenticate with service principal certificate
        resource = "https://management.core.windows.net/"
        authority_url = ("https://login.microsoftonline.com/" + tenant_id)
        context = adal.AuthenticationContext(authority_url)
        return azure_active_directory.AdalAuthentication(
            lambda: context.acquire_token_with_client_certificate(
                resource,
                application_id,
                pem_pkey,
                thumbprint)
        )

    def get_md5_checksum(path):
        """ gets an MD5 hash of a file """
        import hashlib
        md5 = hashlib.md5()
        with open(path, 'rb') as fh:
            for data in iter(lambda: fh.read(4096), b""):
                md5.update(data)
            return md5

    def download_blob(blob_file, local_path):
        """ downloads a file from stroage to local path """
        # Get diretory / file from the blob name
        directoryname, filename = os.path.split(blob_file.name)
        # If there is a direcotry, create it on the local file system if it doesn't exist
        if directoryname:
            if not os.path.exists(os.path.join(local_path, directoryname)):
                os.makedirs((os.path.join(local_path, directoryname)))
        # Download the blob if it is different than local file
        if os.path.exists(os.path.join(local_path, blob.name)):
            object_md5 = get_md5_checksum(os.path.join(local_path, blob_file.name))
            if blob_file.properties.content_settings.content_md5 != base64.b64encode(object_md5.digest()):
                blobservice.get_blob_to_path(storage_account_container_name, blob_file.name, os.path.join(local_path, blob_file.name))
        else:
            blobservice.get_blob_to_path(storage_account_container_name, blob_file.name, os.path.join(local_path, blob_file.name))

    # Check that required arguments are specified
    if (local_file_path is None
            or storage_resource_group is None
            or storage_account_name is None
            or storage_account_container_name is None):
        raise ValueError("local direcotry, storage resource group, storage account, and container must be specified as arguments")

    # Authenticate to Azure resource manager
    automation_runas_connection = automationassets.get_automation_connection("AzureRunAsConnection")
    azure_credential = get_automation_runas_credential(automation_runas_connection)
    subscription_id = str(automation_runas_connection["SubscriptionId"])

    # Get storage key
    storage_client = azure.mgmt.storage.StorageManagementClient(
        azure_credential,
        subscription_id)

    storage_keys = storage_client.storage_accounts.list_keys(storage_resource_group, storage_account_name)
    storage_account_key = storage_keys.keys[0].value
    # Authenticate to the storage account
    blobservice = BlockBlobService(account_name=storage_account_name, account_key=storage_account_key)
    # If local directory does not exist, create it
    if not os.path.exists(local_file_path):
        os.makedirs(local_file_path)

    blobs = blobservice.list_blobs(storage_account_container_name)
    # Dowload all blobs from the container and create local file system to match
    for blob in blobs:
        download_blob(blob, local_file_path)
  
# Copy the pytz package from the pytz container in the storage account to the local python packages        
install_packages("c:\Python27\Lib\site-packages", "pythonmodules", "pythonmodules", "pytz")
import pytz
print pytz.common_timezones


