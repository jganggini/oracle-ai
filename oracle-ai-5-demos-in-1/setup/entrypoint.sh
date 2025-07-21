
oci session authenticate --no-browser --profile-name DEFAULT

echo "A connection between the app and the database is required."
echo "Please, create a safe password for the wallet. It must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter and one number. Avoid using special characters."
read -p "Enter the wallet password: " wallet_password
if [[ -z "$wallet_password" ]]; then
    echo "Wallet password cannot be empty. Exiting."
    exit 1
fi
echo "Creating wallet with the provided password..."    

read -p "Enter the Autonomous Database OCID: " autonomous_database_id
if [[ -z "$autonomous_database_id" ]]; then
    echo "Autonomous Database OCID cannot be empty. Exiting."
    exit 1
fi

echo "Before continuing, please paste the following public key in the Oracle Cloud Console for your Autonomous Database:"
cat ~/.oci/oci_api_key_public.pem
read -p "Press A once you have pasted the public key in the Oracle Cloud Console: " confirmation
if [[ "$confirmation" != "A" ]]; then
    echo "You must paste the public key in the Oracle Cloud Console before proceeding. Exiting."
    exit 1
fi

echo "Generating wallet for Autonomous Database with ID: $autonomous_database_id and password $wallet_password..."

sleep 1m

oci db autonomous-database generate-wallet --autonomous-database-id $autonomous_database_id --password $wallet_password --file ./wallet.zip
if [ $? -ne 0 ]; then
    echo "Failed to generate wallet. Please check your Autonomous Database ID and try again."
    exit 1
fi
unzip -o ./wallet.zip -d ../app/wallet/

python set_environment.py