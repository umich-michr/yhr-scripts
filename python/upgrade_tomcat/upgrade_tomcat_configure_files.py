# The safest and most reliable way to install paramiko and lxml without affecting your system Python is to use a virtual environment.
# This isolates your project’s dependencies and avoids the externally-managed-environment error.

# Create a virtual environment
# python3 -m venv ~/development/scripts/tomcat_venv

# Activate the virual environment:
# source ~/development/scripts/tomcat_venv/bin/activate

# Update pip:
# python -m pip install --upgrade pip

# Install paramiko and lxml
# pip install paramiko lxml

# Configure vscode to use virtual environment
# in vscode, cmd+shift+p -> Python: Select Interpretor -> ~/development/scripts/tomcat_venv
from io import StringIO
import sys
import time
import paramiko
import os
from lxml import etree
import getpass

# Configuration
NEW_VERSION = "11.0.7"
PREVIOUS_VERSION = "11.0.5"
OJDBC_VERSION = "17"
DOWNLOAD_URL = f"https://dlcdn.apache.org/tomcat/tomcat-11/v{NEW_VERSION}/bin/apache-tomcat-{NEW_VERSION}.tar.gz"
TOMCAT_INSTALL_DIR = "/app/apps/rhel8/apache-tomcat"
NEW_TOMCAT_FOLDER = f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}"
TEMP_TOMCAT_FOLDER = f"{TOMCAT_INSTALL_DIR}/apache-tomcat-{NEW_VERSION}"
TOMCAT_ARCHIVE_FILE = f"{TEMP_TOMCAT_FOLDER}/apache-tomcat.tar.gz"
USER_GROUP = "tomcat:michr-developers"
SERVER_XML = f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}/conf/server.xml"
CONTEXT_XML = f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}/conf/context.xml"
MANAGER_WEB_XML = f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}/webapps/manager/WEB-INF/web.xml"
HOST_MANAGER_WEB_XML = (
    f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}/webapps/host-manager/WEB-INF/web.xml"
)
SERVERS = [
    "nabu-test",
    "yhr-umich-test",
    "yhr-itm-test",
    "yhr-umiami-test",
    "yhr-uic-test",
    "yhr-demo-test",
]

SSH_KEY_PATH = "~/.ssh/id_rsa"  # Path to your SSH private key

# Server-specific certificate hostnames
CERT_HOSTS = {
    "nabu-test": "michr-ap-ds20a",
    "yhr-umich-test": "michr-ap-ds15a",
    "yhr-itm-test": "michr-ap-ds16a",
    "yhr-umiami-test": "michr-ap-ds17a",
    "yhr-uic-test": "michr-ap-ds18a",
    "yhr-demo-test": "michr-ap-ds19a",
    "nabu-prod": "michr-ap-ps13a",
    "yhr-umich-prod": "michr-ap-ps14a",
    "yhr-itm-prod": "michr-ap-ps15a",
    "yhr-umiami-prod": "michr-ap-ps16a",
    "yhr-uic-prod": "michr-ap-ps17a",
    "yhr-demo-prod": "michr-ap-ps18a",
}

# server to TNS name mappings
SERVER_TNS_MAPPINGS = {
    "yhr-umich-test": "YHR_UMICH_TEST",
    "yhr-itm-test": "YHR_ITM_TEST",
    "yhr-umiami-test": "YHR_UMIAMI_TEST",
    "yhr-uic-test": "YHR_UIC_TEST",
    "yhr-demo-test": "YHR_DEMO_TEST",
    "yhr-umich-prod": "YHR_UMICH",
    "yhr-itm-prod": "YHR_ITM",
    "yhr-umiami-prod": "YHR_UMIAMI",
    "yhr-uic-prod": "YHR_UIC",
    "yhr-demo-prod": "YHR_DEMO",
}


def get_confirmation():
    """
    Ask the user for confirmation before proceeding with tomcat configuration.
    Returns True if the user confirms, False otherwise.
    """
    print("\n" + "=" * 80)
    print(f"TOMCAT CONFIGURATION CONFIRMATION - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(
        f"You are about to configure Apache Tomcat version {NEW_VERSION} to the following servers:"
    )

    for idx, server in enumerate(SERVERS, 1):
        print(f"  {idx}. {server}")

    print("\nThis operation will:")
    print(f" 1. Download tomcat {NEW_VERSION}")
    print(
        f" 2. Copy ojdbc{OJDBC_VERSION}.jar, oraclepki.jar, ucp{OJDBC_VERSION}.jar and war file from {PREVIOUS_VERSION} if available"
    )
    print(f" 3. Update {SERVER_XML}")
    print(f" 4. Update {CONTEXT_XML}")
    print(f" 5. Update {MANAGER_WEB_XML}")
    print(f" 6. Update {HOST_MANAGER_WEB_XML}")
    print("\nWARNING: This operation is irreversible.")
    print("=" * 80)

    while True:
        response = (
            input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
        )
        if response in ["yes", "y"]:
            print("\nProceeding with tomcat configuration...\n")

            # Additional verification with server count
            verify = input(
                f"Please confirm by typing the number of servers being updated ({len(SERVERS)}): "
            )
            if verify.strip() == str(len(SERVERS)):
                print(
                    f"\nConfirmation received. Starting tomcat {NEW_VERSION} configuration...\n"
                )
                return True
            else:
                print("\nConfirmation failed. Aborted.\n")
                return False
        elif response in ["no", "n"]:
            print("\n Cancelled by user.\n")
            return False
        else:
            print("Please answer 'yes' or 'no'.")


def run_ssh_command(ssh, command, sudo=False):
    """Execute a command over SSH, optionally with sudo."""
    if sudo:
        command = f"sudo {command}"
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode() + stderr.read().decode()
    if exit_status != 0:
        raise RuntimeError(f"Command '{command}' failed: {output}")
    return output


def ssh_connect(server):
    """Establish an SSH connection using SSH config for hostname resolution."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load SSH config to use the same hostname resolution as your terminal
    ssh_config = paramiko.SSHConfig()
    user_config_file = os.path.expanduser("~/.ssh/config")
    if os.path.exists(user_config_file):
        with open(user_config_file) as f:
            ssh_config.parse(f)

    # Get hostname configuration from SSH config
    host_config = ssh_config.lookup(server)

    try:
        # Use config-provided hostname if available, otherwise use server name
        hostname = host_config.get("hostname", server)
        username = host_config.get("user", getpass.getuser())
        key_filename = host_config.get(
            "identityfile", [os.path.expanduser(SSH_KEY_PATH)]
        )
        if isinstance(key_filename, list) and key_filename:
            key_filename = key_filename[0]

        print(f"Connecting to {hostname} as {username}...")
        ssh.connect(
            hostname=hostname, username=username, key_filename=key_filename, timeout=10
        )
        return ssh
    except Exception as e:
        raise RuntimeError(f"Failed to connect to {server}: {e}")


def download_and_extract(ssh, server):
    """Download and extract the Tomcat archive."""
    print(f"[{server}] Downloading and configuring necessary files...")

    # Check if temp folder exists and handle accordingly
    print(f"[{server}] Preparing temp folder {TEMP_TOMCAT_FOLDER}...")
    try:
        # Use test -d to check if the directory exists
        run_ssh_command(ssh, f"test -d {TEMP_TOMCAT_FOLDER}")
        # If no exception, folder exists, so empty it
        print(f"[{server}] Emptying existing folder {TEMP_TOMCAT_FOLDER}...")
        run_ssh_command(ssh, f"rm -rf {TEMP_TOMCAT_FOLDER}/*", sudo=True)
    except RuntimeError:
        # If test -d fails, folder doesn't exist, so create it
        print(f"[{server}] Creating temp folder {TEMP_TOMCAT_FOLDER}...")
        run_ssh_command(ssh, f"mkdir -p {TEMP_TOMCAT_FOLDER}", sudo=True)

    # Download archive
    print(f"[{server}] Downloading Apache Tomcat archive...")
    run_ssh_command(ssh, f"wget -O {TOMCAT_ARCHIVE_FILE} {DOWNLOAD_URL}", sudo=True)

    # Validate archive
    output = run_ssh_command(ssh, f"file -b {TOMCAT_ARCHIVE_FILE}")
    if "gzip" not in output.lower():
        raise RuntimeError(f"[{server}] Downloaded file is not a valid gzip archive")

    # Extract archive
    print(f"[{server}] Extracting Apache Tomcat archive...")
    run_ssh_command(
        ssh, f"tar -xzvf {TOMCAT_ARCHIVE_FILE} -C {TEMP_TOMCAT_FOLDER}", sudo=True
    )
    run_ssh_command(ssh, f"rm -f {TOMCAT_ARCHIVE_FILE}", sudo=True)

    # Move extracted files
    print(f"[{server}] Preparing new folder {NEW_TOMCAT_FOLDER}...")
    try:
        # Check if NEW_TOMCAT_FOLDER exists
        run_ssh_command(ssh, f"test -d {NEW_TOMCAT_FOLDER}")
        # If it exists, remove the entire folder
        print(f"[{server}] Removing existing folder {NEW_TOMCAT_FOLDER}...")
        run_ssh_command(ssh, f"rm -rf {NEW_TOMCAT_FOLDER}", sudo=True)
    except RuntimeError:
        # If it doesn't exist, no action needed before creating
        print(
            f"[{server}] Folder {NEW_TOMCAT_FOLDER} does not exist, will create it..."
        )

    # Create the folder (needed after removal or if it didn't exist)
    print(f"[{server}] Creating new folder {NEW_TOMCAT_FOLDER}...")
    run_ssh_command(ssh, f"mkdir -p {NEW_TOMCAT_FOLDER}", sudo=True)

    # Move extracted files
    print(f"[{server}] Moving extracted files...")
    run_ssh_command(
        ssh,
        f"mv {TEMP_TOMCAT_FOLDER}/apache-tomcat-{NEW_VERSION}/* {NEW_TOMCAT_FOLDER}",
        sudo=True,
    )
    # Delete temp folder
    print(f"[{server}] Deleting {TEMP_TOMCAT_FOLDER}...")
    run_ssh_command(
        ssh,
        f"rm -rf {TEMP_TOMCAT_FOLDER}",
        sudo=True,
    )


def configure_files(ssh, server):
    """Configure ownership, permissions, and copy files from previous version."""
    print(f"[{server}] Updating ownership and permissions...")
    run_ssh_command(ssh, f"chown -R {USER_GROUP} {NEW_TOMCAT_FOLDER}", sudo=True)
    run_ssh_command(ssh, f"chmod -R g+rw {NEW_TOMCAT_FOLDER}/conf", sudo=True)
    run_ssh_command(ssh, f"chmod g+x {NEW_TOMCAT_FOLDER}/conf", sudo=True)

    # Copy configuration files
    print(f"[{server}] Copying configuration files from version {PREVIOUS_VERSION}...")
    try:
        run_ssh_command(
            ssh,
            f"cp -rp {TOMCAT_INSTALL_DIR}/{PREVIOUS_VERSION}/conf/Catalina/ {NEW_TOMCAT_FOLDER}/conf/",
            sudo=True,
        )
    except RuntimeError:
        print(
            f"[{server}] Warning: Previous version configuration directory not found, skipping"
        )

    # Remove logs directory from new version so that later we can add symlink
    print(f"[{server}] Deleting logs folder from new version...")
    run_ssh_command(ssh, f"rm -rf {NEW_TOMCAT_FOLDER}/logs/", sudo=True)

    # Copy libraries and web applications
    print(f"[{server}] Copying libraries and web applications...")
    for lib in [
        f"ojdbc{OJDBC_VERSION}.jar",
        "oraclepki.jar",
        f"ucp{OJDBC_VERSION}.jar",
    ]:
        try:
            run_ssh_command(
                ssh,
                f"cp -p {TOMCAT_INSTALL_DIR}/{PREVIOUS_VERSION}/lib/{lib} {NEW_TOMCAT_FOLDER}/lib/.",
                sudo=True,
            )
        except RuntimeError:
            print(f"[{server}] Warning: Library {lib} not found, skipping")

    # Check which WAR file to copy based on server name
    if server in ["nabu-test", "nabu-prod"]:
        war_file = "nabu-backend.war"
    else:
        war_file = "backend.war"

    try:
        run_ssh_command(
            ssh,
            f"cp -p {TOMCAT_INSTALL_DIR}/{PREVIOUS_VERSION}/webapps/{war_file} {NEW_TOMCAT_FOLDER}/webapps/.",
            sudo=True,
        )
    except RuntimeError:
        print(f"[{server}] Warning: {war_file} not found, skipping")


def update_server_xml(ssh, server, cert_host):
    """Update server.xml by replacing Realm and placing all Connectors at the start of Service."""
    print(f"[{server}] Updating server.xml configurations...")

    # Backup server.xml
    run_ssh_command(ssh, f"cp {SERVER_XML} {SERVER_XML}.bak", sudo=True)

    # Download server.xml locally for modification
    sftp = ssh.open_sftp()
    temp_local_file = "server.xml.temp"
    sftp.get(SERVER_XML, temp_local_file)
    sftp.close()

    # Parse XML
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(temp_local_file, parser)
    root = tree.getroot()

    # Remove comments
    for comment in root.xpath("//comment()"):
        parent = comment.getparent()
        if parent is not None:
            comment.getparent().remove(comment)

    # Get Service element
    service = root.find(".//Service[@name='Catalina']")
    if service is None:
        raise RuntimeError(f"[{server}] No Service element found in {SERVER_XML}")

    # 1. Remove existing connectors only
    connectors = service.findall("Connector")
    print(f"[{server}] Removing {len(connectors)} existing connectors")
    for connector in connectors:
        service.remove(connector)

    # Add HTTP connector with trailing whitespace
    print(f"[{server}] Adding HTTP connector (port 8080)")
    http_connector = etree.Element("Connector")
    http_connector.set("port", "8080")
    http_connector.set("protocol", "HTTP/1.1")
    http_connector.set("connectionTimeout", "20000")
    http_connector.set("redirectPort", "8443")
    http_connector.tail = "\n    "
    service.insert(0, http_connector)

    # Add SSL connector using etree.Element
    print(
        f"[{server}] Adding SSL connector (port 8443) with certificate for {cert_host}"
    )
    ssl_connector = etree.Element("Connector")
    ssl_connector.set("port", "8443")
    ssl_connector.set("SSLEnabled", "true")
    ssl_connector.set("scheme", "https")
    ssl_connector.set("secure", "true")
    ssl_connector.tail = "\n    "

    # Create SSL Host Config
    ssl_host_config = etree.SubElement(ssl_connector, "SSLHostConfig")
    ssl_host_config.set(
        "ciphers",
        "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384",
    )
    ssl_host_config.set("disableSessionTickets", "true")
    ssl_host_config.set("honorCipherOrder", "false")
    ssl_host_config.set("protocols", "+TLSv1.2, +TLSv1.3")
    ssl_host_config.tail = "\n        "

    # Create Certificate
    certificate = etree.SubElement(ssl_host_config, "Certificate")
    certificate.set(
        "certificateFile", f"/app/certificates/public/{cert_host}.med.umich.edu.crt"
    )
    certificate.set(
        "certificateKeyFile", f"/app/certificates/private/{cert_host}.med.umich.edu.key"
    )
    certificate.tail = "\n    "

    # Create Upgrade Protocol
    upgrade_protocol = etree.SubElement(ssl_connector, "UpgradeProtocol")
    upgrade_protocol.set("className", "org.apache.coyote.http2.Http2Protocol")
    upgrade_protocol.tail = "\n    "

    service.insert(1, ssl_connector)

    # Add AJP connector
    print(f"[{server}] Adding AJP connector (port 8009)")
    ajp_connector = etree.Element("Connector")
    ajp_connector.set("protocol", "AJP/1.3")
    ajp_connector.set("address", "127.0.0.1")
    ajp_connector.set("port", "8009")
    ajp_connector.set("secretRequired", "false")
    ajp_connector.set("redirectPort", "8443")
    ajp_connector.set("tomcatAuthentication", "false")
    ajp_connector.set("allowedRequestAttributesPattern", ".*")
    ajp_connector.tail = "\n\n    "  # Extra newline after the last connector
    service.insert(2, ajp_connector)

    # 2. Update LockOutRealm
    print(f"[{server}] Updating Realms")
    engine = service.find("Engine")
    if engine is None:
        raise RuntimeError(f"[{server}] No Engine element found in {SERVER_XML}")

    lockout_realm = engine.find(
        ".//Realm[@className='org.apache.catalina.realm.LockOutRealm']"
    )
    if lockout_realm is None:
        raise RuntimeError(f"[{server}] No LockOutRealm found in {SERVER_XML}")

    # Clear existing realm children
    realm_children = list(lockout_realm)
    print(f"[{server}] Removing {len(realm_children)} existing realm configurations")
    for child in realm_children:
        lockout_realm.remove(child)

    # Add JNDI Realm
    print(f"[{server}] Adding JNDI Realm for LDAP authentication")
    jndi_realm = etree.Element("Realm")
    jndi_realm.set("className", "org.apache.catalina.realm.JNDIRealm")
    jndi_realm.set("connectionURL", "ldaps://ldap.ent.med.umich.edu:636")
    jndi_realm.set("userBase", "ou=people,dc=med,dc=umich,dc=edu")
    jndi_realm.set("userSearch", "(uid={0})")
    jndi_realm.set("userRoleName", "memberOf")
    jndi_realm.set("roleBase", "ou=groups,dc=med,dc=umich,dc=edu")
    jndi_realm.set("roleName", "cn")
    jndi_realm.set("roleSearch", "(member={0})")
    jndi_realm.tail = "\n        "
    lockout_realm.append(jndi_realm)

    # Add UserDatabase Realm with SecretKeyCredentialHandler
    print(f"[{server}] Adding UserDatabase Realm with SecretKeyCredentialHandler")
    user_realm = etree.Element("Realm")
    user_realm.set("className", "org.apache.catalina.realm.UserDatabaseRealm")
    user_realm.set("resourceName", "UserDatabase")
    user_realm.tail = "\n      "

    # Add CredentialHandler
    credential_handler = etree.SubElement(user_realm, "CredentialHandler")
    credential_handler.set(
        "className", "org.apache.catalina.realm.SecretKeyCredentialHandler"
    )
    credential_handler.set("algorithm", "PBKDF2WithHmacSHA512")
    credential_handler.set("keyLength", "512")
    credential_handler.tail = "\n        "

    lockout_realm.append(user_realm)

    # 3. Update Host and Access Log Valve
    print(f"[{server}] Updating Host and AccessLogValve settings")
    host = engine.find(".//Host[@name='localhost']")
    if host is not None:
        host.set("autoDeploy", "false")

        valve = host.find(
            ".//Valve[@className='org.apache.catalina.valves.AccessLogValve']"
        )
        if valve is not None:
            valve.set("rotatable", "false")
            valve.set("requestAttributesEnabled", "true")

    # Write the modified XML to temp file
    tree.write(
        temp_local_file, encoding="utf-8", xml_declaration=True, pretty_print=True
    )

    # Perform string-based validation for key elements
    with open(temp_local_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Basic string validation - check for required elements
    validation_errors = []

    if 'port="8080"' not in content:
        validation_errors.append("Missing HTTP Connector (port 8080)")

    if 'port="8443"' not in content:
        validation_errors.append("Missing SSL Connector (port 8443)")

    if f"/app/certificates/public/{cert_host}.med.umich.edu.crt" not in content:
        validation_errors.append(f"Missing certificate path for {cert_host}")

    if 'protocol="AJP/1.3"' not in content:
        validation_errors.append("Missing AJP Connector")

    if 'className="org.apache.catalina.realm.JNDIRealm"' not in content:
        validation_errors.append("Missing JNDI Realm")

    if 'algorithm="PBKDF2WithHmacSHA512"' not in content:
        validation_errors.append(
            "Missing CredentialHandler with PBKDF2WithHmacSHA512 algorithm"
        )

    if 'autoDeploy="false"' not in content:
        validation_errors.append("Host autoDeploy not set to false")

    if (
        'rotatable="false"' not in content
        or 'requestAttributesEnabled="true"' not in content
    ):
        validation_errors.append("AccessLogValve missing required attributes")

    # Raise error if any validation failed
    if validation_errors:
        error_message = f"[{server}] Validation failed:\n" + "\n".join(
            validation_errors
        )
        raise RuntimeError(error_message)

    # Upload the file to the server
    temp_remote_file = f"/tmp/server.xml.working"
    sftp = ssh.open_sftp()
    sftp.put(temp_local_file, temp_remote_file)
    sftp.close()

    # move the new file to the correct location and set file permission
    run_ssh_command(ssh, f"mv {temp_remote_file} {SERVER_XML}", sudo=True)
    run_ssh_command(ssh, f"chown {USER_GROUP} {SERVER_XML}", sudo=True)

    # Clean up
    run_ssh_command(ssh, f"rm {SERVER_XML}.bak", sudo=True)
    os.remove(temp_local_file)
    print(f"[{server}] server.xml configurations updated successfully")


def update_context_xml(ssh, server, tns_name):
    """Update context.xml"""
    print(f"[{server}] Updating context.xml configuration...")

    # Decide which configuration to apply based on server name
    if server.startswith("nabu-"):
        # Get correct configuration based on environment (test/prod)
        if "test" in server:
            res_name = "jdbc/nabuTestDataSource"
            url = "jdbc:oracle:thin:@//MRSD.MCIT.MED.UMICH.EDU:1521/MRSD.WORLD"
        else:
            res_name = "jdbc/nabuDataSource"
            url = "jdbc:oracle:thin:@//MHRP.MCIT.MED.UMICH.EDU:1521/MHRP.WORLD"
        return modify_context_xml(
            ssh, server, lambda root: modify_nabu_context_xml(root, url, res_name)
        )
    else:
        res_name = "jdbc/yhrDataSource"
        url = f"jdbc:oracle:thin:@{tns_name}?TNS_ADMIN=/app/db/network/admin"
        return modify_context_xml(
            ssh, server, lambda root: modify_yhr_context_xml(root, url, res_name)
        )


def modify_context_xml(ssh, server, create_resources_fn):
    """Common helper to modify context.xml with a specific resource creation function."""
    # Backup context.xml
    run_ssh_command(ssh, f"cp {CONTEXT_XML} {CONTEXT_XML}.bak", sudo=True)

    # Download context.xml locally for modification
    sftp = ssh.open_sftp()
    temp_local_file = "context.xml"
    sftp.get(CONTEXT_XML, temp_local_file)
    sftp.close()

    # Parse XML while preserving whitespace
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(temp_local_file, parser)
    root = tree.getroot()

    # Apply server-specific resource creation (using the passed function)
    validation_errors = create_resources_fn(root)

    # Write the modified XML to temp file
    tree.write(temp_local_file, encoding="utf-8", xml_declaration=True)

    # Handle validation errors if any
    if validation_errors:
        os.remove(temp_local_file)
        error_message = f"[{server}] Validation failed:\n" + "\n".join(
            validation_errors
        )
        raise RuntimeError(error_message)

    # Upload the file to the server
    print(f"[{server}] Uploading modified context.xml to the server")
    temp_remote_file = "/tmp/context.xml"
    sftp = ssh.open_sftp()
    sftp.put(temp_local_file, temp_remote_file)
    sftp.close()

    # Move the new file to the correct location and set file permission
    run_ssh_command(ssh, f"mv {temp_remote_file} {CONTEXT_XML}", sudo=True)
    run_ssh_command(ssh, f"chown {USER_GROUP} {CONTEXT_XML}", sudo=True)

    # Clean up
    os.remove(temp_local_file)
    print(f"[{server}] context.xml updated successfully")
    return True


def modify_yhr_context_xml(root, url, res_name):
    """Create YHR-specific resources for context.xml."""
    print(f"Adding YHR Environment and JDBC Resource configuration...")
    validation_errors = []

    # Create Environment element for properties file
    env_element = etree.Element("Environment")
    env_element.set("name", "configuration.properties.file")
    env_element.set(
        "value",
        f"/app/apps/rhel8/apache-tomcat/tomcat/conf/Catalina/localhost/backend.properties",
    )
    env_element.set("type", "java.lang.String")
    env_element.set("override", "false")
    env_element.tail = "\n\n    "

    # Create Resource element for database connection
    res_element = etree.Element("Resource")
    res_element.set("name", res_name)
    res_element.set("auth", "Container")
    res_element.set("factory", "oracle.ucp.jdbc.PoolDataSourceImpl")
    res_element.set("connectionFactoryClassName", "oracle.jdbc.pool.OracleDataSource")
    res_element.set("type", "oracle.ucp.jdbc.PoolDataSource")
    res_element.set(
        "description", "Oracle UCP JNDI Connection Pool for YourHealthResearch"
    )
    res_element.set("maxActive", "")
    res_element.set("maxIdle", "10")
    res_element.set("maxWait", "-1")
    res_element.set("url", url)
    res_element.set("initialPoolSize", "3")
    res_element.set("minPoolSize", "3")
    res_element.set("maxPoolSize", "100")
    res_element.set("maxStatements", "100")
    res_element.set("connectionWaitTimeout", "30")
    res_element.set("inactiveConnectionTimeout", "3600")
    res_element.set("validateConnectionOnBorrow", "true")
    res_element.tail = "\n"

    # Format indentation based on existing elements
    format_xml_indentation(root, env_element, res_element)

    # Verify elements after writing
    modified_parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(
        StringIO(etree.tostring(root, encoding="utf-8").decode()), modified_parser
    )
    modified_root = tree.getroot()

    # Verification checks
    env_elements = modified_root.xpath(
        "//Environment[@name='configuration.properties.file']"
    )
    if not env_elements:
        validation_errors.append("Failed to add Environment element")

    resource_elements = modified_root.xpath("//Resource[@name='jdbc/yhrDataSource']")
    if not resource_elements:
        validation_errors.append("Failed to add Resource element")

    return validation_errors


def modify_nabu_context_xml(root, url, res_name):
    """Create Nabu-specific resources for context.xml."""
    print("Adding Nabu JDBC Resource configuration...")
    validation_errors = []

    # Create Resource element for database connection
    res_element = etree.Element("Resource")
    res_element.set("name", res_name)
    res_element.set("auth", "Container")
    res_element.set("factory", "oracle.ucp.jdbc.PoolDataSourceImpl")
    res_element.set("connectionFactoryClassName", "oracle.jdbc.pool.OracleDataSource")
    res_element.set("type", "oracle.ucp.jdbc.PoolDataSource")
    res_element.set("description", "Oracle UCP JNDI Connection Pool for DCR")
    res_element.set("maxActive", "20")
    res_element.set("maxIdle", "10")
    res_element.set("maxWait", "-1")
    res_element.set("user", "")
    res_element.set("password", "")
    res_element.set("url", url)
    res_element.set("initialPoolSize", "3")
    res_element.set("minPoolSize", "3")
    res_element.set("maxPoolSize", "100")
    res_element.set("maxStatements", "100")
    res_element.set("connectionWaitTimeout", "30")
    res_element.set("inactiveConnectionTimeout", "3600")
    res_element.set("validateConnectionOnBorrow", "true")
    res_element.tail = "\n"

    # Format indentation
    format_xml_indentation(root, None, res_element)

    # Verify elements after writing
    modified_parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(
        StringIO(etree.tostring(root, encoding="utf-8").decode()), modified_parser
    )
    modified_root = tree.getroot()

    # Verification check
    resource_elements = modified_root.xpath(f"//Resource[@name='{res_name}']")
    if not resource_elements:
        validation_errors.append(f"Failed to add Resource element {res_name}")

    return validation_errors


def format_xml_indentation(root, first_element, last_element):
    """Format XML indentation for context.xml elements."""
    # Find the last child element to determine where to add new elements
    last_child = None
    for child in root:
        last_child = child

    # Add proper indentation before the first element if needed
    if last_child is not None:
        if not last_child.tail:
            last_child.tail = "\n\n    "
        elif not last_child.tail.endswith("\n\n    "):
            if last_child.tail.endswith("\n    "):
                last_child.tail += "\n    "
            elif last_child.tail.endswith("\n"):
                last_child.tail += "    "
            else:
                last_child.tail += "\n\n    "

    # Add elements to the root
    if first_element is not None:
        root.append(first_element)
    root.append(last_element)

    # Format the closing tag indentation
    if last_element.tail:
        if not last_element.tail.endswith("\n"):
            last_element.tail += "\n"


def update_manager_web_xml(ssh, server):
    """Update manager web.xml by replacing role-names in security-constraints."""
    print(f"[{server}] Updating manager web.xml role configurations...")

    # Backup web.xml
    run_ssh_command(ssh, f"cp {MANAGER_WEB_XML} {MANAGER_WEB_XML}.bak", sudo=True)

    # Download web.xml locally for modification
    sftp = ssh.open_sftp()
    temp_local_file = "manager.web.xml"
    sftp.get(MANAGER_WEB_XML, temp_local_file)
    sftp.close()

    # Parse XML while preserving whitespace and comments
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(temp_local_file, parser)
    root = tree.getroot()

    # Define the namespace
    ns = {"j": "https://jakarta.ee/xml/ns/jakartaee"}

    # Helper function to add security roles at a position in a parent element
    def add_security_roles(parent, position):
        # Add comment
        comment = etree.Comment(" Security roles referenced by this web application ")
        comment.tail = "\n  "
        parent.insert(position, comment)
        position += 1

        # First role: michr-developers
        dev_role = etree.Element("{%s}security-role" % ns["j"])
        dev_role.tail = "\n  "

        dev_desc = etree.SubElement(dev_role, "{%s}description" % ns["j"])
        dev_desc.text = (
            "\n    The role that grants full administrator access defined in LDAP\n    "
        )
        dev_desc.tail = "\n    "

        dev_role_name = etree.SubElement(dev_role, "{%s}role-name" % ns["j"])
        dev_role_name.text = "michr-developers"
        dev_role_name.tail = "\n  "

        parent.insert(position, dev_role)
        position += 1

        # Second role: michr-aux-login
        aux_role = etree.Element("{%s}security-role" % ns["j"])
        aux_role.tail = "\n\n  "  # Extra newline before the next element

        aux_desc = etree.SubElement(aux_role, "{%s}description" % ns["j"])
        aux_desc.text = "\n      The role that is required to access the text Manager pages defined in LDAP.\n          This role should only have one user assigned to it, and it is michr-jenkins.\n    "
        aux_desc.tail = "\n    "

        aux_role_name = etree.SubElement(aux_role, "{%s}role-name" % ns["j"])
        aux_role_name.text = "michr-aux-login"
        aux_role_name.tail = "\n  "

        parent.insert(position, aux_role)

        return position + 1

    # Track roles added to each security constraint
    modified_constraints = {
        "htmlManager": [],
        "textManager": [],
        "jmxProxy": [],
        "status": [],
    }

    # Find all security constraints with namespace
    security_constraints = root.findall(".//j:security-constraint", namespaces=ns)

    # Process each security constraint
    for constraint in security_constraints:
        # Get the web resource name to identify which constraint we're working with
        resource_name = constraint.find(".//j:web-resource-name", namespaces=ns)
        if resource_name is None:
            continue

        resource_name_text = resource_name.text

        # Find the auth-constraint element
        auth_constraint = constraint.find(".//j:auth-constraint", namespaces=ns)
        if auth_constraint is None:
            continue

        # Remove all existing role-name elements
        for role in auth_constraint.findall(".//j:role-name", namespaces=ns):
            auth_constraint.remove(role)

        # Add new role-names based on the resource name
        if "HTML Manager interface" in resource_name_text:
            # Add michr-developers for HTML Manager
            role_name = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name.text = "michr-developers"
            role_name.tail = "\n    "
            modified_constraints["htmlManager"].append("michr-developers")

        elif "Text Manager interface" in resource_name_text:
            # Add michr-developers and michr-aux-login for Text Manager
            role_name1 = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name1.text = "michr-developers"
            role_name1.tail = "\n       "
            modified_constraints["textManager"].append("michr-developers")

            role_name2 = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name2.text = "michr-aux-login"
            role_name2.tail = "\n   "
            modified_constraints["textManager"].append("michr-aux-login")

        elif "JMX Proxy interface" in resource_name_text:
            # Add michr-developers for JMX Proxy
            role_name = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name.text = "michr-developers"
            role_name.tail = "\n    "
            modified_constraints["jmxProxy"].append("michr-developers")

        elif "Status interface" in resource_name_text:
            # Add michr-developers and michr-aux-login for Status
            role_name1 = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name1.text = "michr-developers"
            role_name1.tail = "\n       "
            modified_constraints["status"].append("michr-developers")

            role_name2 = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name2.text = "michr-aux-login"
            role_name2.tail = "\n   "
            modified_constraints["status"].append("michr-aux-login")

    # Remove all existing security-role elements
    for security_role in root.findall(".//j:security-role", namespaces=ns):
        root.remove(security_role)

    # Remove security roles comment
    for comment in root.xpath("//comment()"):
        if "Security roles referenced by this web application" in comment.text:
            parent = comment.getparent()
            if parent is not None:
                parent.remove(comment)

    # Find the position of the first error-page
    error_page = root.find(".//j:error-page", namespaces=ns)
    if error_page is not None:
        # Get the parent of error-page (should be the root element)
        parent = error_page.getparent()
        if parent is not None:
            # Find the position of error-page in its parent's children
            position = list(parent).index(error_page)
            add_security_roles(parent, position)
    else:
        # If error-page not found, add to the end of the root element
        add_security_roles(root, len(list(root)))

    # Write the modified XML to temp file
    tree.write(temp_local_file, encoding="utf-8", xml_declaration=True)

    # Validate the exact roles set for each constraint
    validation_errors = []

    # HTML Manager should have only michr-developers
    if not modified_constraints["htmlManager"]:
        validation_errors.append("HTML Manager interface not found")
    elif set(modified_constraints["htmlManager"]) != {"michr-developers"}:
        validation_errors.append(
            f"HTML Manager has incorrect roles: {modified_constraints['htmlManager']}, expected: ['michr-developers']"
        )

    # Text Manager should have michr-developers and michr-aux-login
    if not modified_constraints["textManager"]:
        validation_errors.append("Text Manager interface not found")
    elif set(modified_constraints["textManager"]) != {
        "michr-developers",
        "michr-aux-login",
    }:
        validation_errors.append(
            f"Text Manager has incorrect roles: {modified_constraints['textManager']}, expected: ['michr-developers', 'michr-aux-login']"
        )

    # JMX Proxy should have only michr-developers
    if not modified_constraints["jmxProxy"]:
        validation_errors.append("JMX Proxy interface not found")
    elif set(modified_constraints["jmxProxy"]) != {"michr-developers"}:
        validation_errors.append(
            f"JMX Proxy has incorrect roles: {modified_constraints['jmxProxy']}, expected: ['michr-developers']"
        )

    # Status should have michr-developers and michr-aux-login
    if not modified_constraints["status"]:
        validation_errors.append("Status interface not found")
    elif set(modified_constraints["status"]) != {"michr-developers", "michr-aux-login"}:
        validation_errors.append(
            f"Status has incorrect roles: {modified_constraints['status']}, expected: ['michr-developers', 'michr-aux-login']"
        )

    # Raise error if any validation failed
    if validation_errors:
        error_message = f"[{server}] Validation failed:\n" + "\n".join(
            validation_errors
        )
        raise RuntimeError(error_message)

    # Validate security roles
    security_roles = root.findall(".//j:security-role/j:role-name", namespaces=ns)
    role_names = [role.text for role in security_roles]
    if set(role_names) != {"michr-developers", "michr-aux-login"}:
        validation_errors.append(
            f"Security roles incorrect: {role_names}, expected: ['michr-developers', 'michr-aux-login']"
        )

    print(f"[{server}] Role validation successful:")
    print(f"  HTML Manager: {modified_constraints['htmlManager']}")
    print(f"  Text Manager: {modified_constraints['textManager']}")
    print(f"  JMX Proxy: {modified_constraints['jmxProxy']}")
    print(f"  Status: {modified_constraints['status']}")
    print(f"  Security Roles: {role_names}")

    # Upload the file to the server
    print("Uploading modified file to the server")
    temp_remote_file = f"/tmp/manager.web.xml"
    sftp = ssh.open_sftp()
    sftp.put(temp_local_file, temp_remote_file)
    sftp.close()

    # move the new file to the correct location and set file permission
    run_ssh_command(ssh, f"mv {temp_remote_file} {MANAGER_WEB_XML}", sudo=True)
    run_ssh_command(ssh, f"chown {USER_GROUP} {MANAGER_WEB_XML}", sudo=True)

    # Clean up
    run_ssh_command(ssh, f"rm {MANAGER_WEB_XML}.bak", sudo=True)
    os.remove(temp_local_file)
    print(f"[{server}] Manager web.xml configurations updated successfully")
    return True


def update_host_manager_web_xml(ssh, server):
    """Update host-manager web.xml by replacing role-names in security-constraints."""
    print(f"[{server}] Updating host-manager web.xml role configurations...")

    # Backup web.xml
    run_ssh_command(
        ssh, f"cp {HOST_MANAGER_WEB_XML} {HOST_MANAGER_WEB_XML}.bak", sudo=True
    )

    # Download web.xml locally for modification
    sftp = ssh.open_sftp()
    temp_local_file = "host-manager.web.xml"
    sftp.get(HOST_MANAGER_WEB_XML, temp_local_file)
    sftp.close()

    # Parse XML while preserving whitespace and comments
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(temp_local_file, parser)
    root = tree.getroot()

    # Define the namespace
    ns = {"j": "https://jakarta.ee/xml/ns/jakartaee"}

    # Helper function to add security roles at a position in a parent element
    def add_security_roles(parent, position):
        # Add comment
        comment = etree.Comment(" Security roles referenced by this web application ")
        comment.tail = "\n  "
        parent.insert(position, comment)
        position += 1

        # First role: michr-developers
        dev_role = etree.Element("{%s}security-role" % ns["j"])
        dev_role.tail = "\n  "

        dev_desc = etree.SubElement(dev_role, "{%s}description" % ns["j"])
        dev_desc.text = (
            "\n    The role that grants full administrator access defined in LDAP\n    "
        )
        dev_desc.tail = "\n    "

        dev_role_name = etree.SubElement(dev_role, "{%s}role-name" % ns["j"])
        dev_role_name.text = "michr-developers"
        dev_role_name.tail = "\n  "

        parent.insert(position, dev_role)

    # Track roles added to each security constraint
    modified_constraints = {
        "hostManager": [],
        "htmlHostManager": [],
    }

    # Find all security constraints with namespace
    security_constraints = root.findall(".//j:security-constraint", namespaces=ns)

    # Process each security constraint
    for constraint in security_constraints:
        # Get the web resource name to identify which constraint we're working with
        resource_name = constraint.find(".//j:web-resource-name", namespaces=ns)
        if resource_name is None:
            continue

        resource_name_text = resource_name.text

        # Find the auth-constraint element
        auth_constraint = constraint.find(".//j:auth-constraint", namespaces=ns)
        if auth_constraint is None:
            continue

        # Remove all existing role-name elements
        for role in auth_constraint.findall(".//j:role-name", namespaces=ns):
            auth_constraint.remove(role)

        # Add new role-names based on the resource name
        if resource_name_text == "HostManager commands":
            # Add michr-developers for Host Manager
            role_name = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name.text = "michr-developers"
            role_name.tail = "\n    "
            modified_constraints["hostManager"].append("michr-developers")

        elif resource_name_text == "HTMLHostManager commands":
            # Add michr-developers for HTML Host Manager
            role_name = etree.SubElement(auth_constraint, "{%s}role-name" % ns["j"])
            role_name.text = "michr-developers"
            role_name.tail = "\n       "
            modified_constraints["htmlHostManager"].append("michr-developers")

    # Remove all existing security-role elements
    for security_role in root.findall(".//j:security-role", namespaces=ns):
        root.remove(security_role)

    # Remove security roles comment
    for comment in root.xpath("//comment()"):
        if "Security roles referenced by this web application" in comment.text:
            parent = comment.getparent()
            if parent is not None:
                parent.remove(comment)

    # Find the position of the first error-page
    error_page = root.find(".//j:error-page", namespaces=ns)
    if error_page is not None:
        # Get the parent of error-page (should be the root element)
        parent = error_page.getparent()
        if parent is not None:
            # Find the position of error-page in its parent's children
            position = list(parent).index(error_page)
            add_security_roles(parent, position)
    else:
        # If error-page not found, add to the end of the root element
        add_security_roles(root, len(list(root)))

    # Write the modified XML to temp file
    tree.write(temp_local_file, encoding="utf-8", xml_declaration=True)

    # Validate the exact roles set for each constraint
    validation_errors = []

    # Host Manager should have only michr-developers
    if not modified_constraints["hostManager"]:
        validation_errors.append("Host Manager commands not found")
    elif set(modified_constraints["hostManager"]) != {"michr-developers"}:
        validation_errors.append(
            f"Host Manager has incorrect roles: {modified_constraints['hostManager']}, expected: ['michr-developers']"
        )

    # Html Host Manager should have michr-developers
    if not modified_constraints["htmlHostManager"]:
        validation_errors.append("Html Host Manager commands not found")
    elif set(modified_constraints["htmlHostManager"]) != {"michr-developers"}:
        validation_errors.append(
            f"Html Host Manager has incorrect roles: {modified_constraints['htmlHostManager']}, expected: ['michr-developers']"
        )

    # Raise error if any validation failed
    if validation_errors:
        error_message = f"[{server}] Validation failed:\n" + "\n".join(
            validation_errors
        )
        raise RuntimeError(error_message)

    # Validate security roles
    security_roles = root.findall(".//j:security-role/j:role-name", namespaces=ns)
    role_names = [role.text for role in security_roles]
    if set(role_names) != {"michr-developers"}:
        validation_errors.append(
            f"Security roles incorrect: {role_names}, expected: ['michr-developers']"
        )

    print(f"[{server}] Role validation successful:")
    print(f"  Host Manager: {modified_constraints['hostManager']}")
    print(f"  Html Host Manager: {modified_constraints['htmlHostManager']}")
    print(f"  Security Roles: {role_names}")

    # Upload the file to the server
    print("Uploading modified file to the server")
    temp_remote_file = f"/tmp/host-manager.web.xml"
    sftp = ssh.open_sftp()
    sftp.put(temp_local_file, temp_remote_file)
    sftp.close()

    # move the new file to the correct location and set file permission
    run_ssh_command(ssh, f"mv {temp_remote_file} {HOST_MANAGER_WEB_XML}", sudo=True)
    run_ssh_command(ssh, f"chown {USER_GROUP} {HOST_MANAGER_WEB_XML}", sudo=True)

    # Clean up
    run_ssh_command(ssh, f"rm {HOST_MANAGER_WEB_XML}.bak", sudo=True)
    os.remove(temp_local_file)
    print(f"[{server}] Host-manager web.xml configurations updated successfully")
    return True


def display_final_warnings():
    """Display final warnings after script execution."""
    print("\n" + "=" * 80)
    print(f"IMPORTANT WARNINGS")
    print("=" * 80)
    print("\n⚠️  MANUAL ACTION REQUIRED:")
    print("    For security reasons, you must manually update the following:")
    print(f"    1. Go to nabu-test server and add the user/password in {CONTEXT_XML}")
    print(f"    2. Go to nabu-prod server and add the user/password in {CONTEXT_XML}")
    print("\n    Command to edit:")
    print(f"    $ sudo vim {CONTEXT_XML}")
    print("\n    Specifically look for the Resource elements:")
    print("    - jdbc/nabuTestDataSource (on nabu-test)")
    print("    - jdbc/nabuDataSource (on nabu-prod)")
    print("\n    Make sure the user and password attributes are set correctly.")
    print("\n    This warning was generated by automated script.")
    print("=" * 80)
    print()


def main():
    # Get confirmation before proceeding
    if not get_confirmation():
        sys.exit(0)

    has_nabu_servers = False

    for server in SERVERS:

        if server in ["nabu-test", "nabu-prod"]:
            has_nabu_servers = True

        print(
            f"============================================\nStarting Tomcat {NEW_VERSION} configuration on {server}...\n============================================"
        )

        # Get certificate host
        cert_host = CERT_HOSTS.get(server, "michr-ap-ds15a")
        if not cert_host:
            raise RuntimeError(
                f"[{server}] No certificate host mapping found for server {server}"
            )

        print(f"[{server}] Using host {cert_host} for certificate")

        # Get the appropriate TNS name for this server
        if server in ["nabu-test", "nabu-prod"]:
            # For nabu servers, TNS name is not needed
            print(
                f"[{server}] Skipping TNS configuration - not required for nabu servers"
            )
            tns_name = None  # Set to None or any default value as needed
        else:
            # For other servers, get the TNS name from mappings
            tns_name = SERVER_TNS_MAPPINGS.get(server)
            if not tns_name:
                raise RuntimeError(
                    f"[{server}] No TNS name mapping found for server {server}"
                )
            print(f"[{server}] Using TNS name: {tns_name} for database connection")

        try:
            # Connect to server
            ssh = ssh_connect(server)

            # Perform tasks
            download_and_extract(ssh, server)
            configure_files(ssh, server)
            update_server_xml(ssh, server, cert_host)
            update_context_xml(ssh, server, tns_name)
            update_manager_web_xml(ssh, server)
            update_host_manager_web_xml(ssh, server)

            print(
                f"[{server}]  Configuration for Apache Tomcat {NEW_VERSION} completed."
            )

            ssh.close()
        except Exception as e:
            print(f"[{server}] Unexpected error occurred: {e}")
            ssh.close()
            exit(1)

    if has_nabu_servers:
        # Display final warnings
        display_final_warnings()


if __name__ == "__main__":
    main()
