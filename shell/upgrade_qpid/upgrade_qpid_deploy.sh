#!/bin/bash

# Define variables
NEW_VERSION="9.2.1"
PREVIOUS_VERSION="9.2.0"
QPID_INSTALL_DIR="/app/apps/rhel8/qpid-broker"
QPID_SERVICE_NAME="qpid-broker"
YHR_ROUTING_SERVICE_NAME="yhr-routing"
TOMCAT_SERVICE_NAME="tomcat"
SYMBOLIC_LINK="$QPID_INSTALL_DIR/qpid-broker"
USER_GROUP="qpid-broker:michr-developers"
SERVERS=("yhr-umich-test" "yhr-demo-test" "yhr-uic-test" "yhr-umiami-test" "yhr-itm-test")

# Function to get confirmation from user
get_confirmation() {
  echo
  echo "================================================================================"
  echo "QPID BROKER DEPLOYMENT CONFIRMATION"
  echo "================================================================================"
  echo "You are about to deploy Qpid Broker version $NEW_VERSION to the following servers:"

  local server_count=0
  for SERVER in "${SERVERS[@]}"; do
    server_count=$((server_count + 1))
    echo "  $server_count. $SERVER"
  done

  echo
  echo "This operation will:"
  echo "  1. Stop the running Qpid Broker service"
  echo "  2. Create symbolic links to the new version"
  echo "  3. Update ownership settings"
  echo "  4. Restart Qpid Broker, Tomcat and yhr-routing services"
  echo
  echo "WARNING: This operation will cause service interruption."
  echo "================================================================================"

  while true; do
    echo
    read -p "Are you sure you want to proceed? (yes/no): " response
    case $response in
    [Yy]es | [Yy])
      echo
      echo "Proceeding with deployment..."
      echo
      # Additional verification with server count
      read -p "Please confirm by typing the number of servers being updated (${#SERVERS[@]}): " verify
      if [[ "$verify" == "${#SERVERS[@]}" ]]; then
        echo
        echo "Confirmation received. Starting deployment..."
        echo
        return 0
      else
        echo
        echo "Confirmation failed. Deployment aborted."
        echo
        return 1
      fi
      ;;
    [Nn]o | [Nn])
      echo
      echo "Deployment cancelled by user."
      echo
      return 1
      ;;
    *)
      echo "Please answer 'yes' or 'no'."
      ;;
    esac
  done
}

# Function to print deployment summary
print_summary() {
  echo
  echo "================================================================================"
  echo "DEPLOYMENT SUMMARY"
  echo "================================================================================"

  local success_count=0
  for i in "${!SERVERS[@]}"; do
    if [[ "${RESULTS[$i]}" == "SUCCESS" ]]; then
      echo "✅ ${SERVERS[$i]}: ${RESULTS[$i]}"
      success_count=$((success_count + 1))
    else
      echo "❌ ${SERVERS[$i]}: ${RESULTS[$i]}"
    fi
  done

  echo "--------------------------------------------------------------------------------"
  echo "Total servers: ${#SERVERS[@]}"
  echo "Successful deployments: $success_count"
  echo "Failed deployments: $((${#SERVERS[@]} - success_count))"
  echo "================================================================================"

  if [[ $success_count -ne ${#SERVERS[@]} ]]; then
    echo
    echo "WARNING: Not all deployments were successful!"
    exit 1
  else
    echo
    echo "All deployments completed successfully!"
    exit 0
  fi
}

# Start script execution

# Get confirmation before proceeding
get_confirmation || exit 0

# Initialize results array
declare -a RESULTS

# Deploy to each server
for i in "${!SERVERS[@]}"; do
  SERVER=${SERVERS[$i]}
  echo
  echo "================================================================================"
  echo "Deploying Qpid Broker update on $SERVER..."
  echo "================================================================================"

  ssh -q -o ConnectTimeout=10 "$SERVER" "
    set -e  # Stop execution if any command fails

    # Step 1: Stop the Qpid Broker service
    echo '[$SERVER] Stopping $QPID_SERVICE_NAME service...'
    sudo systemctl stop \"$QPID_SERVICE_NAME\" || { echo \"[$SERVER] Error: Failed to stop $QPID_SERVICE_NAME service\"; exit 1; }

    # Verify service has stopped
    echo '[$SERVER] Verifying $QPID_SERVICE_NAME has stopped...'
    if sudo systemctl is-active \"$QPID_SERVICE_NAME\" > /dev/null 2>&1; then
      echo \"[$SERVER] Warning: $QPID_SERVICE_NAME is still running after stop command. Waiting...\"
      sleep 10
      if sudo systemctl is-active \"$QPID_SERVICE_NAME\" > /dev/null 2>&1; then
        echo \"[$SERVER] Warning: $QPID_SERVICE_NAME did not stop properly. Proceeding anyway.\"
      fi
    else
      echo \"[$SERVER] $QPID_SERVICE_NAME service has stopped successfully\"
    fi

    # Step 2: Copy the qpidwork directory from the old version, if it exists and set correct permissions
    if [ -d "$QPID_INSTALL_DIR/$PREVIOUS_VERSION/qpidwork" ]; then
      echo 'Copying qpidwork directory from version $PREVIOUS_VERSION...'
      sudo cp -R "$QPID_INSTALL_DIR/$PREVIOUS_VERSION/qpidwork" "$QPID_INSTALL_DIR/$NEW_VERSION/qpidwork" || { echo "[$SERVER] Error: Failed to copy qpidwork directory"; exit 1; }
      sudo chown -R "$USER_GROUP" "$QPID_INSTALL_DIR/$NEW_VERSION/qpidwork" || { echo "[$SERVER] Error: Failed to update ownership for qpidwork directory"; exit 1; }
    else
      echo "[$SERVER] Warning: Directory $QPID_INSTALL_DIR/$PREVIOUS_VERSION/qpidwork not found, skipping copy step"
    fi

    # Step 3: Create or update the symbolic link for the new version
    echo '[$SERVER] Updating symbolic link...'
    sudo ln -sfn \"$NEW_VERSION\" \"$SYMBOLIC_LINK\" || { echo \"[$SERVER] Error: Failed to update symbolic link\"; exit 1; }

    # Verify symbolic link was created correctly
    if [ \"\$(readlink -f \"$SYMBOLIC_LINK\")\" != \"$QPID_INSTALL_DIR/$NEW_VERSION\" ]; then
      echo \"[$SERVER] Error: Symbolic link verification failed\"; 
      echo \"[$SERVER] Expected: $NEW_VERSION\"; 
      echo \"[$SERVER] Actual: \$(readlink -f \"$SYMBOLIC_LINK\")\"; 
      exit 1;
    fi
    echo \"[$SERVER] Symbolic link verified successfully\"

    # Step 4: Update ownership for the symbolic link
    echo '[$SERVER] Updating ownership of the symbolic link...'
    sudo chown -h \"$USER_GROUP\" \"$SYMBOLIC_LINK\" || { echo \"[$SERVER] Error: Failed to update ownership for symbolic link\"; exit 1; }
    echo \"[$SERVER] Ownership updated successfully\"
  
    # Step 5: Restart Qpid Broker service
    echo '[$SERVER] Restarting $QPID_SERVICE_NAME service...'
    sudo systemctl restart \"$QPID_SERVICE_NAME\" || { echo \"[$SERVER] Error: Failed to restart $QPID_SERVICE_NAME\"; exit 1; }

    # Verify service has started
    echo '[$SERVER] Verifying $QPID_SERVICE_NAME has started...'
    timeout=60
    interval=5
    elapsed=0
    while [ \$elapsed -lt \$timeout ]; do
      if sudo systemctl is-active \"$QPID_SERVICE_NAME\" > /dev/null 2>&1; then
        echo \"[$SERVER] $QPID_SERVICE_NAME service is now running\"
        break
      fi
      echo \"[$SERVER] $QPID_SERVICE_NAME is still starting... waiting \${interval} seconds\"
      sleep \$interval
      elapsed=\$((elapsed + interval))
    done

    if [ \$elapsed -ge \$timeout ]; then
      echo \"[$SERVER] Error: $QPID_SERVICE_NAME failed to start within \${timeout} seconds\";
      exit 1;
    fi

    # Step 6: Restart Tomcat service
    echo '[$SERVER] Restarting $TOMCAT_SERVICE_NAME service...'
    sudo systemctl restart \"$TOMCAT_SERVICE_NAME\" || { echo \"[$SERVER] Error: Failed to restart $TOMCAT_SERVICE_NAME\"; exit 1; }

    # Verify Tomcat service has started
    echo '[$SERVER] Verifying $TOMCAT_SERVICE_NAME has started...'
    timeout=90
    interval=10
    elapsed=0
    while [ \$elapsed -lt \$timeout ]; do
      if sudo systemctl is-active \"$TOMCAT_SERVICE_NAME\" > /dev/null 2>&1; then
        echo \"[$SERVER] $TOMCAT_SERVICE_NAME service is now running\"
        break
      fi
      echo \"[$SERVER] $TOMCAT_SERVICE_NAME is still starting... waiting \${interval} seconds\"
      sleep \$interval
      elapsed=\$((elapsed + interval))
    done

    if [ \$elapsed -ge \$timeout ]; then
      echo \"[$SERVER] Error: $TOMCAT_SERVICE_NAME failed to start within \${timeout} seconds\";
      exit 1;
    fi

    # Step 7: Restart yhr-routing service
    echo '[$SERVER] Restarting $YHR_ROUTING_SERVICE_NAME service...'
    sudo systemctl restart \"$YHR_ROUTING_SERVICE_NAME\" || { echo \"[$SERVER] Error: Failed to restart $YHR_ROUTING_SERVICE_NAME\"; exit 1; }

    # Verify service has started
    echo '[$SERVER] Verifying $YHR_ROUTING_SERVICE_NAME has started...'
    timeout=60
    interval=5
    elapsed=0
    while [ \$elapsed -lt \$timeout ]; do
      if sudo systemctl is-active \"$YHR_ROUTING_SERVICE_NAME\" > /dev/null 2>&1; then
        echo \"[$SERVER] $YHR_ROUTING_SERVICE_NAME service is now running\"
        break
      fi
      echo \"[$SERVER] $YHR_ROUTING_SERVICE_NAME is still starting... waiting \${interval} seconds\"
      sleep \$interval
      elapsed=\$((elapsed + interval))
    done

    if [ \$elapsed -ge \$timeout ]; then
      echo \"[$SERVER] Error: $YHR_ROUTING_SERVICE_NAME failed to start within \${timeout} seconds\";
      exit 1;
    fi

    # Display version information
    echo \"[$SERVER] Deployed Qpid Broker version: $NEW_VERSION\"
    echo \"[$SERVER] Qpid Broker update completed successfully.\"
    exit 0
  "

  # Store the result for this server
  if [ $? -eq 0 ]; then
    RESULTS[$i]="SUCCESS"
    echo "[$SERVER] Qpid Broker deployment completed successfully."
  else
    RESULTS[$i]="FAILED"
    echo "[$SERVER] Unexpected error occurred during Qpid Broker update"
  fi
done

# Print deployment summary
print_summary
