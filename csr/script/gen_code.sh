#!/bin/bash -f
GEN_STRUCT_CONV=true

CSV_SOURCE=https://docs.google.com/spreadsheets/d/1-6EV7ZmCIKY5moo7pextqfhPewN-1DB3yZNYqQXBMas
CSR_LIST=./csr_list.csv
OUT_FILE_DEF_ADDR=./model/csr/include/csr_define.hcodal
#OUT_FILE_DEF_MASK=./model/csr/include/csr_define_mask.hcodal
OUT_FILE_STRUCT_REG=./model/csr/include/csr_struct_reg.codal
OUT_FILE_STRUCT_CONV=./model/csr/modules/csr_data_conv.codal
OUT_FILE_STRUCT_WIRE=./model/csr/include/csr_struct_wire.codal
UPDT_FILE_CSR=./model/csr/modules/csr.codal
git

#clean
rm $OUT_FILE_DEF_ADDR
#rm $OUT_FILE_DEF_MASK
rm $OUT_FILE_STRUCT_REG
rm $OUT_FILE_STRUCT_WIRE

## Download and export to CSV
#curl -Lo $CSR_LIST "$CSV_SOURCE/export?gid=230178269&format=csv"
#echo "Orginal CSV tables downloaded from https://docs.google.com/spreadsheets/d/1-6EV7ZmCIKY5moo7pextqfhPewN-1DB3yZNYqQXBMas"

./script/gen_define_addr.py $CSR_LIST $OUT_FILE_DEF_ADDR
echo "Code generated for ./model/include/csr_define_addr.hcodal"

#./script/gen_define_mask.py $CSR_LIST $OUT_FILE_DEF_MASK
#echo "Code generated for ./model/include/csr_define_mask.hcodal"

./script/gen_struct_reg.py $CSR_LIST $OUT_FILE_STRUCT_REG$OUT_FILE_STRUCT_REG $OUT_FILE_STRUCT_CONV
#./script/gen_struct_reg.py $CSR_LIST $OUT_FILE_STRUCT_REG
echo "Code generated for ./model/include/csr_struct_reg.codal"
echo "Code generated for ./model/modules/csr_data_conv.codal"

./script/gen_struct_wire.py $CSR_LIST $OUT_FILE_STRUCT_WIRE
echo "Code generated for ./model/include/csr_struct_wire.codal"

./script/gen_csr.py $CSR_LIST $UPDT_FILE_CSR
echo "Code inserted in ./model/modules/csr.codal"
