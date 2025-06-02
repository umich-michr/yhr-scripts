#!/bin/bash
BACKUP_FOLDER_NAME="23.5.0.24.07"
OLD_JDBC_SUPPORT_FILES=("oraclepki.jar" "ucp11.jar" "ojdbc11.jar")
NEW_JDBC_SUPPORT_FILES=("oraclepki.jar" "ucp17.jar" "ojdbc17.jar")
DOWNLOAD_URL="https://download.oracle.com/otn-pub/otn_software/jdbc/237/ojdbc17-full.tar.gz"
DOWNLOADED_JDBC_ARCHIVE_NAME="ojdbc17-full.tar.gz"
TAR_EXTRACT_DIR_NAME="ojdbc17-full"

# A pretend Python dictionary with bash 3
# ssh server alias vs $CATALINA_HOME
SERVERS=("nabu-test:/app/apps/rhel8/apache-tomcat/tomcat"
  "yhr-demo-test:/app/apps/rhel8/apache-tomcat/tomcat"
  "yhr-uic-test:/app/apps/rhel8/apache-tomcat/tomcat"
  "yhr-umiami-test:/app/apps/rhel8/apache-tomcat/tomcat"
  "yhr-itm-test:/app/apps/rhel8/apache-tomcat/tomcat"
  "yhr-umich-test:/app/apps/rhel8/apache-tomcat/tomcat"
)

get_confirmation() {
  echo
  echo "================================================================================"
  echo "JDBC DRIVER UPDATE CONFIRMATION"
  echo "================================================================================"
  echo "You are about to update JDBC drivers on the following servers:"

  local server_count=0
  for SERVER in "${SERVERS[@]}"; do
    server_count=$((server_count + 1))
    echo "  $server_count. $SERVER"
  done

  echo
  echo "This operation will:"
  echo "  1. Download $DOWNLOADED_JDBC_ARCHIVE_NAME"
  echo "  2. Copy the following JDBC support files to tomcat library:"
  for file in "${NEW_JDBC_SUPPORT_FILES[@]}"; do
    echo "     - $file"
  done
  echo "  3. Update ownership of the copied jdbc files to tomcat:michr-developers"
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
        echo "Confirmation received. Upgrading JDBC drivers..."
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

for server in "${SERVERS[@]}"; do
  SERVER=${server%%:*}
  TOMCAT_LIB=${server#*:}/lib
  USER_HOME=$(ssh -q "$SERVER" "echo \$HOME")
  BACKUP_FOLDER="$USER_HOME/$BACKUP_FOLDER_NAME"
  TAR_EXTRACT_DIR="$USER_HOME/$TAR_EXTRACT_DIR_NAME"
  #To know if the target server is intended for prod or test use by the server connection alias naming convention
  SERVER_USAGE=$(echo "$SERVER" | cut -d "-" -f 3)
  if [[ "$SERVER_USAGE" == "test" ]]; then
    echo "Running against TEST instance"
  else
    echo "Running against ***PROD*** instance!!"
  fi

  printf "User home is: %s, old jdbc backup dir is: %s, the downloaded archive will be extracted to: %s \n" "$USER_HOME" "$BACKUP_FOLDER" "$TAR_EXTRACT_DIR"
  printf "%s has tomcat lib folder: %s \n" "$SERVER" "$TOMCAT_LIB"

  ssh -q "$SERVER" "wget -qP $USER_HOME $DOWNLOAD_URL"
  echo "New jdbc archive is downloaded"

  ssh -q "$SERVER" "mkdir $TAR_EXTRACT_DIR"

  ssh -q "$SERVER" "tar -xvf $DOWNLOADED_JDBC_ARCHIVE_NAME --directory $TAR_EXTRACT_DIR"
  echo "New jdbc driver archive is unpacked"

  ssh -q "$SERVER" "mkdir $BACKUP_FOLDER"

  #BACKUP THE OLD JDBC FILES
  for old_jdbc_file in "${OLD_JDBC_SUPPORT_FILES[@]}"; do
    ssh -q "$SERVER" "sudo mv $TOMCAT_LIB/$old_jdbc_file $BACKUP_FOLDER/"
  done

  #COPY THE NEW JDBC FILES TO TOMCAT LIB
  for new_jdbc_file in "${NEW_JDBC_SUPPORT_FILES[@]}"; do
    ssh -q "$SERVER" "sudo cp $TAR_EXTRACT_DIR/$new_jdbc_file $TOMCAT_LIB/"
  done

  #CHANGE THE FILE PERMISSIONS OF NEWLY COPIED FILES
  for new_jdbc_file in "${NEW_JDBC_SUPPORT_FILES[@]}"; do
    ssh -q "$SERVER" "sudo chown tomcat:michr-developers $TOMCAT_LIB/$new_jdbc_file"
  done

  for i in "${!OLD_JDBC_SUPPORT_FILES[@]}"; do
    new_jdbc_file="${NEW_JDBC_SUPPORT_FILES[i]}"
    old_jdbc_file="${OLD_JDBC_SUPPORT_FILES[i]}"
    printf "%s vs %s for file size and date \n" "new_jdbc_file" "old_jdbc_file"
    ssh -q "$SERVER" "ls -l $TOMCAT_LIB/$new_jdbc_file $BACKUP_FOLDER/$old_jdbc_file|awk -F' ' -v OFS='\t' '{print \$5, \$6, \$7, \$8 }'"
  done

  ssh -q "$SERVER" "sudo rm -rf $TAR_EXTRACT_DIR $DOWNLOADED_JDBC_ARCHIVE_NAME"
  echo "Files downloaded and extracted for jdbc update are removed"

  ssh -q "$SERVER" "tar -czvf \"$BACKUP_FOLDER_NAME\".tar.gz $BACKUP_FOLDER_NAME"
  ssh -q "$SERVER" "rm -rf $BACKUP_FOLDER"

  # restart tomcat after the upgrade
  # ssh -q "$SERVER" "sudo systemctl restart tomcat"
  # echo "Tomcat stopped and started"
done

#To test the map logic used in the loop above
#echo -e "${SERVERS[1]%%:*} server has its tomcat home set to: ${SERVERS[1]#*:}\n"
