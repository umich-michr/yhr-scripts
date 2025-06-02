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

import time
import paramiko
import os
import getpass
import sys

NEW_VERSION = "11.0.7"
TOMCAT_INSTALL_DIR = "/app/apps/rhel8/apache-tomcat"
TOMCAT_LOGS_FOLDER = "/app/log/tomcat/"
NEW_TOMCAT_FOLDER = f"{TOMCAT_INSTALL_DIR}/{NEW_VERSION}"
TOMCAT_SYMBOLIC_LINK = f"{TOMCAT_INSTALL_DIR}/tomcat"
TOMCAT_LOGS_SYMBOLIC_LINK = f"{NEW_TOMCAT_FOLDER}/logs"
USER_GROUP = "tomcat:michr-developers"
SERVERS = [
    "nabu-test",
    "yhr-umich-test",
    "yhr-itm-test",
    "yhr-umiami-test",
    "yhr-uic-test",
    "yhr-demo-test",
]

SSH_KEY_PATH = "~/.ssh/id_rsa"  # Path to your SSH private key


def get_confirmation():
    """
    Ask the user for confirmation before proceeding with deployment.
    Returns True if the user confirms, False otherwise.
    """
    print("\n" + "=" * 80)
    print(f"TOMCAT DEPLOYMENT CONFIRMATION - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(
        f"You are about to deploy Apache Tomcat version {NEW_VERSION} to the following servers:"
    )

    for idx, server in enumerate(SERVERS, 1):
        print(f"  {idx}. {server}")

    print("\nThis operation will:")
    print("  1. Stop the running Tomcat service")
    print("  2. Create symbolic links to the new version")
    print("  3. Start the Tomcat service with the new version")
    print("\nWARNING: This operation will cause service interruption.")
    print("=" * 80)

    while True:
        response = (
            input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
        )
        if response in ["yes", "y"]:
            print("\nProceeding with deployment...\n")

            # Additional verification with server count
            verify = input(
                f"Please confirm by typing the number of servers being updated ({len(SERVERS)}): "
            )
            if verify.strip() == str(len(SERVERS)):
                print("\nConfirmation received. Starting deployment...\n")
                return True
            else:
                print("\nConfirmation failed. Deployment aborted.\n")
                return False
        elif response in ["no", "n"]:
            print("\nDeployment cancelled by user.\n")
            return False
        else:
            print("Please answer 'yes' or 'no'.")


def check_nabu_credentials():
    """
    Check if any Nabu servers are in the deployment list and confirm credentials were updated.
    """
    nabu_servers = [server for server in SERVERS if server.startswith("nabu-")]

    if not nabu_servers:
        return True  # No Nabu servers, no need for this check

    print("\n" + "=" * 80)
    print(f"NABU SERVERS CREDENTIAL CHECK - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("The following Nabu servers are included in this deployment:")

    for idx, server in enumerate(nabu_servers, 1):
        print(f"  {idx}. {server}")

    print("\nIMPORTANT: For Nabu servers, you must manually update:")
    print("  - The database user and password in context.xml")
    print("\nLocation: /app/apps/rhel8/apache-tomcat/11.0.7/conf/context.xml")
    print("Resources: jdbc/nabuTestDataSource or jdbc/nabuDataSource")
    print("=" * 80)

    while True:
        response = (
            input(
                "\nHave you already updated the credentials for all Nabu servers? (yes/no): "
            )
            .strip()
            .lower()
        )
        if response in ["yes", "y"]:
            print("\nProceeding with deployment...\n")
            return True
        elif response in ["no", "n"]:
            print("\nPlease update the credentials before proceeding with deployment.")
            print("Deployment cancelled.\n")
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


def deploy_new_tomcat(ssh, server):
    """
    Deploy the new Tomcat by creating symbolic links and restarting the service.
    This is the final step in the upgrade process.
    """
    print(f"[{server}] Deploying new Tomcat installation...")

    try:
        # Stop Tomcat service
        print(f"[{server}] Stopping Tomcat service...")
        run_ssh_command(ssh, "systemctl stop tomcat", sudo=True)

        # Check if Tomcat has stopped with a timeout
        print(f"[{server}] Verifying Tomcat has stopped...")
        max_wait_seconds = 30
        wait_interval = 3
        total_waited = 0

        while total_waited < max_wait_seconds:
            # Check if tomcat is active
            exit_code = ssh.exec_command("sudo systemctl is-active tomcat")[
                1
            ].channel.recv_exit_status()

            # Exit code 3 means service is inactive (stopped)
            if exit_code == 3:
                print(f"[{server}] Tomcat service has stopped successfully")
                break

            print(
                f"[{server}] Tomcat is still stopping... waiting {wait_interval} seconds"
            )
            time.sleep(wait_interval)
            total_waited += wait_interval

        if total_waited >= max_wait_seconds:
            print(
                f"[{server}] WARNING: Tomcat may not have fully stopped after {max_wait_seconds} seconds. Proceeding anyway."
            )
            # Force kill any remaining Tomcat processes if needed
            run_ssh_command(
                ssh, "pkill -9 -f catalina.base", sudo=True, check_error=False
            )
            time.sleep(2)

        # Create symbolic link for logs directory
        print(
            f"[{server}] Creating symbolic link from {TOMCAT_LOGS_FOLDER} to {TOMCAT_LOGS_SYMBOLIC_LINK}..."
        )
        run_ssh_command(
            ssh,
            f"ln -sfn {TOMCAT_LOGS_FOLDER} {TOMCAT_LOGS_SYMBOLIC_LINK}",
            sudo=True,
        )
        run_ssh_command(
            ssh, f"chown -h {USER_GROUP} {TOMCAT_LOGS_SYMBOLIC_LINK}", sudo=True
        )

        # Verify logs symlink was created properly
        logs_link = run_ssh_command(
            ssh, f"ls -la {TOMCAT_LOGS_SYMBOLIC_LINK}", sudo=True
        )
        if TOMCAT_LOGS_FOLDER not in logs_link:
            raise RuntimeError(
                f"[{server}] Failed to create logs symbolic link properly"
            )

        # Create main Tomcat symbolic link pointing to new version
        print(
            f"[{server}] Creating symbolic link from {NEW_VERSION} to {TOMCAT_SYMBOLIC_LINK}..."
        )
        run_ssh_command(ssh, f"ln -sfn {NEW_VERSION} {TOMCAT_SYMBOLIC_LINK}", sudo=True)
        run_ssh_command(ssh, f"chown -h {USER_GROUP} {TOMCAT_SYMBOLIC_LINK}", sudo=True)

        # Verify main symlink was created properly
        main_link = run_ssh_command(ssh, f"ls -la {TOMCAT_SYMBOLIC_LINK}", sudo=True)
        if NEW_VERSION not in main_link:
            raise RuntimeError(
                f"[{server}] Failed to create tomcat symbolic link properly"
            )

        # Start Tomcat service
        print(f"[{server}] Starting Tomcat service...")
        start_result = ssh.exec_command("sudo systemctl start tomcat")[
            1
        ].channel.recv_exit_status()

        if start_result != 0:
            raise RuntimeError(
                f"[{server}] Failed to start Tomcat service (exit code: {start_result})"
            )

        # Verify Tomcat is running with timeout
        print(f"[{server}] Verifying Tomcat service is running...")
        max_wait_seconds = 60  # Longer timeout for startup
        wait_interval = 5
        total_waited = 0

        while total_waited < max_wait_seconds:
            # Check if tomcat is active
            exit_code = ssh.exec_command("sudo systemctl is-active tomcat")[
                1
            ].channel.recv_exit_status()

            # Exit code 0 means service is active (running)
            if exit_code == 0:
                print(f"[{server}] Tomcat service is now running")
                break

            print(
                f"[{server}] Tomcat is still starting... waiting {wait_interval} seconds"
            )
            time.sleep(wait_interval)
            total_waited += wait_interval

        if total_waited >= max_wait_seconds:
            raise RuntimeError(
                f"[{server}] Tomcat failed to start within {max_wait_seconds} seconds"
            )

        # Display relevant information
        tomcat_version = run_ssh_command(
            ssh, f"{TOMCAT_SYMBOLIC_LINK}/bin/version.sh | head -n 1", sudo=True
        )
        print(f"[{server}] Deployed version: {tomcat_version}")
        print(f"[{server}] Tomcat {NEW_VERSION} deployed completed")

        return True

    except Exception as e:
        error_message = f"[{server}] Error during deployment: {str(e)}"
        print(error_message)
        raise RuntimeError(error_message)


def main():
    # Get confirmation before proceeding
    if not get_confirmation():
        sys.exit(0)

    # Check Nabu credentials if any Nabu servers are in the list
    if not check_nabu_credentials():
        sys.exit(0)

    # Track deployment results
    results = []

    for server in SERVERS:
        print(
            f"============================================\nDeploying Apache Tomcat update on {server}...\n============================================"
        )

        try:
            # Connect to server
            ssh = ssh_connect(server)

            # Perform tasks
            deploy_new_tomcat(ssh, server)

            results.append((server, "SUCCESS"))
        except Exception as e:
            error_message = f"[{server}] Unexpected error occurred: {e}"
            print(error_message)
            results.append((server, f"FAILED: {str(e)}"))
        finally:
            if ssh:
                ssh.close()
    # Print summary
    print("\n" + "=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)

    success_count = sum(1 for server, status in results if "SUCCESS" in status)

    for server, status in results:
        status_indicator = "✅" if "SUCCESS" in status else "❌"
        print(f"{status_indicator} {server}: {status}")

    print("-" * 80)
    print(f"Total servers: {len(SERVERS)}")
    print(f"Successful deployments: {success_count}")
    print(f"Failed deployments: {len(SERVERS) - success_count}")
    print("=" * 80)

    # Exit with appropriate code
    if success_count != len(SERVERS):
        print("\nWARNING: Not all deployments were successful!")
        sys.exit(1)
    else:
        print("\nAll deployments completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
