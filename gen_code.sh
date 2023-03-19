#!/bin/bash -f

CSV_SOURCE=https://docs.google.com/spreadsheets/d/1-6EV7ZmCIKY5moo7pextqfhPewN-1DB3yZNYqQXBMas
CSR_LIST=./csr_list.csv
OUT_FILE_DEF=./model/csr/include/csr_define.hcodal

OUT_FILE_STRUCT=./model/csr/include/csr_struct.codal
OUT_FILE_CSR_BANK=./model/csr/modules/csr_bank.codal
OUT_FILE_CSR_PORT1=./model/csr/modules/csr_port_declare.txt
OUT_FILE_CSR_PORT2=./model/csr/modules/csr_port_connect.txt

OUT_FILE_STRUCT_32=./model/csr/include/csr_struct_32.codal
OUT_FILE_CSR_BANK_32=./model/csr/modules/csr_bank_32.codal
OUT_FILE_CSR_PORT1_32=./model/csr/modules/csr_port_declare_32.txt
OUT_FILE_CSR_PORT2_32=./model/csr/modules/csr_port_connect_32.txt

# Download and export to CSV
curl -Lo $CSR_LIST "$CSV_SOURCE/export?gid=230178269&format=csv"
echo "Orginal CSV tables downloaded from https://docs.google.com/spreadsheets/d/1-6EV7ZmCIKY5moo7pextqfhPewN-1DB3yZNYqQXBMas"

#Generate struct code from $CSR_LIST
rm $OUT_FILE_DEF
rm $OUT_FILE_STRUCT
rm $OUT_FILE_CSR_BANK
rm $OUT_FILE_CSR_PORT1
rm $OUT_FILE_CSR_PORT2
rm $OUT_FILE_STRUCT_32
rm $OUT_FILE_CSR_BANK_32
rm $OUT_FILE_CSR_PORT1_32
rm $OUT_FILE_CSR_PORT2_32

./gen_csr_define.py $CSR_LIST $OUT_FILE_DEF
echo "Code generated in ./model/include/csr_define.hcodal"

./gen_csr_bank.py $CSR_LIST $OUT_FILE_STRUCT $OUT_FILE_CSR_BANK $OUT_FILE_CSR_PORT1 $OUT_FILE_CSR_PORT2
echo "Code generated in ./model/include/csr_struct.codal"
echo "Code generated in ./model/modules/csr_bank.codal"
echo "Code generated in ./model/modules/csr_port_declare.txt"
echo "Code generated in ./model/modules/csr_port_connect.txt"

./gen_csr_bank_32.py $CSR_LIST $OUT_FILE_STRUCT_32 $OUT_FILE_CSR_BANK_32 $OUT_FILE_CSR_PORT1_32 $OUT_FILE_CSR_PORT2_32
echo "Code generated in ./model/include/csr_struct_32.codal"
echo "Code generated in ./model/modules/csr_bank_32.codal"
echo "Code generated in ./model/modules/csr_port_32_declare.txt"
echo "Code generated in ./model/modules/csr_port_32_connect.txt"