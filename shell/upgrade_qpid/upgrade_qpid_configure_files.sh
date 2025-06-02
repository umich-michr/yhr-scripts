#!/bin/bash

# Define variables
NEW_VERSION="9.2.1"
PREVIOUS_VERSION="9.2.0"
DOWNLOAD_URL="https://archive.apache.org/dist/qpid/broker-j/$NEW_VERSION/binaries/apache-qpid-broker-j-$NEW_VERSION-bin.tar.gz"
QPID_INSTALL_DIR="/app/apps/rhel8/qpid-broker"
NEW_QPID_FOLDER="$QPID_INSTALL_DIR/qpid-broker-$NEW_VERSION"
QPID_ARCHIVE_FILE="$NEW_QPID_FOLDER/qpid-broker.tar.gz"
EXTRACTED_FOLDER="$NEW_QPID_FOLDER/qpid-broker"
USER_GROUP="qpid-broker:michr-developers"
SERVERS=("yhr-umich-test" "yhr-demo-test" "yhr-uic-test" "yhr-umiami-test" "yhr-itm-test")

get_confirmation() {
  echo
  echo "================================================================================"
  echo "QPID BROKER CONFIGURATION CONFIRMATION"
  echo "================================================================================"
  echo "You are about to configure Qpid Broker version $NEW_VERSION to the following servers:"

  local server_count=0
  for SERVER in "${SERVERS[@]}"; do
    server_count=$((server_count + 1))
    echo "  $server_count. $SERVER"
  done

  echo
  echo "This operation will:"
  echo "  1. Download QPID $NEW_VERSION"
  echo "  2. Copy qpidwork directory from $PREVIOUS_VERSION to $NEW_VERSION"
  echo "  3. Update ownership of $NEW_VERSION to $USER_GROUP"
  echo
  echo "WARNING: This operation is irreversible."
  echo "================================================================================"

  while true; do
    echo
    read -p "Are you sure you want to proceed? (yes/no): " response
    case $response in
    [Yy]es | [Yy])
      echo
      echo "Proceeding with configuration..."
      echo
      # Additional verification with server count
      read -p "Please confirm by typing the number of servers being updated (${#SERVERS[@]}): " verify
      if [[ "$verify" == "${#SERVERS[@]}" ]]; then
        echo
        echo "Confirmation received. Starting configuration for QPID $NEW_VERSION..."
        echo
        return 0
      else
        echo
        echo "Confirmation failed. Aborted."
        echo
        return 1
      fi
      ;;
    [Nn]o | [Nn])
      echo
      echo "Cancelled by user."
      echo
      return 1
      ;;
    *)
      echo "Please answer 'yes' or 'no'."
      ;;
    esac
  done
}

# Get confirmation before proceeding
get_confirmation || exit 0

for SERVER in "${SERVERS[@]}"; do
  echo "============================================"
  echo "Starting Qpid Broker update on $SERVER..."
  echo "============================================"

  ssh -q -o ConnectTimeout=10 "$SERVER" "
    set -e  # Stop execution if any command fails

    # Step 1: Create or empty the new version folder
    echo 'Preparing new version folder...'
    if [ -d "$NEW_QPID_FOLDER" ]; then
        echo "[$SERVER] Emptying existing folder $NEW_QPID_FOLDER..."
        sudo rm -rf "$NEW_QPID_FOLDER/"* || { echo "[$SERVER] Error: Failed to empty folder $NEW_QPID_FOLDER"; exit 1; }
    else
        echo "[$SERVER] Creating new version folder $NEW_QPID_FOLDER..."
        sudo mkdir -p "$NEW_QPID_FOLDER" || { echo "[$SERVER] Error: Failed to create folder $NEW_QPID_FOLDER"; exit 1; }
    fi

    # Step 2: download the archive to the NEW_QPID_FOLDER 
    echo 'Downloading Qpid Broker archive to $NEW_QPID_FOLDER...'
    echo 'Download url: $DOWNLOAD_URL...'
    sudo wget -nv -O "$QPID_ARCHIVE_FILE" "$DOWNLOAD_URL" || { echo "[$SERVER] Error: Failed to download Qpid Broker archive"; exit 1; }

    echo "Validating downloaded archive..."
    if [ ! -s "$QPID_ARCHIVE_FILE" ]; then
        echo '[ERROR] Downloaded archive ($QPID_ARCHIVE_FILE) is empty or invalid'
        exit 1
    fi
    file_type=\$(file -b "$QPID_ARCHIVE_FILE")
    if [[ "\$file_type" != *gzip* ]]; then
        echo '[ERROR] Downloaded file is not a valid gzip archive'
        exit 1
    fi

    # Step 3: Extract the archive
    echo 'Extracting Qpid Broker archive in $NEW_QPID_FOLDER...'
    sudo tar -xzvf "$QPID_ARCHIVE_FILE" -C "$NEW_QPID_FOLDER" || { echo "[$SERVER] Error: Failed to extract Qpid Broker archive"; exit 1; }
    # Cleanup archive immediately after extraction
    sudo rm -f "$QPID_ARCHIVE_FILE" || { echo "[$SERVER] Error: Failed to clean up archive file $QPID_ARCHIVE_FILE"; exit 1; }

    # Step 4: Move extracted files to the correct location
    echo 'Moving extracted files...'
    if [ ! -d "$EXTRACTED_FOLDER/$NEW_VERSION" ]; then
      echo "[$SERVER] Error: Expected folder $EXTRACTED_FOLDER/$NEW_VERSION not found after extraction"
      exit 1
    fi

    # Check if destination directory exists
    if [ -d "$QPID_INSTALL_DIR/$NEW_VERSION" ]; then
        echo "[$SERVER] Warning: Destination directory $QPID_INSTALL_DIR/$NEW_VERSION already exists. Emptying the directory..."
        sudo rm -rf "$QPID_INSTALL_DIR/$NEW_VERSION"/* || { echo "[$SERVER] Error: Failed to empty folder $QPID_INSTALL_DIR/$NEW_VERSION"; exit 1; }
    else
        echo "[$SERVER] Creating destination directory $QPID_INSTALL_DIR/$NEW_VERSION..."
        sudo mkdir -p "$QPID_INSTALL_DIR/$NEW_VERSION" || { echo "[$SERVER] Error: Failed to create destination directory $QPID_INSTALL_DIR/$NEW_VERSION"; exit 1; }
    fi

    # Now that we're sure the directory exists, we can safely move the files
    sudo mv "$EXTRACTED_FOLDER/$NEW_VERSION"/* "$QPID_INSTALL_DIR/$NEW_VERSION" || { echo "[$SERVER] Error: Failed to move extracted files"; exit 1; }

    # Step 5: Update ownership for the new version
    echo '[$SERVER] Updating ownership of directory $QPID_INSTALL_DIR/$NEW_VERSION...'
    sudo chown -R "$USER_GROUP" "$QPID_INSTALL_DIR/$NEW_VERSION" || { echo "[$SERVER] Error: Failed to update ownership for $NEW_VERSION"; exit 1; }

    # Step 6: Clean up temporary files and folders
    sudo rm -rf "$NEW_QPID_FOLDER" || { echo "[$SERVER] Error: Failed to clean up temporary files"; exit 1; }

    echo "Qpid Broker $NEW_VERSION configured successfully on $SERVER."
  " || {
    echo "[$SERVER] Unexpected error occurred during Qpid Broker configuration"
    exit 1
  }

done
