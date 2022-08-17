#!/usr/bin/env bash

mkdir -p source/

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/928409f4-4a34-4bec-93c9-61380173df58/download/epd_202104.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202104.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/3a608346-73ff-4b58-aec2-935fb9f765e6/download/epd_202105.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202105.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/24291a1c-f47a-40fc-a4df-1d062b21adfb/download/epd_202106.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202106.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/a3644305-ac6a-4aa9-a4b0-ffd8f4a788fe/download/epd_202107.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202107.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/7c6ce8dc-0b10-4a22-a54d-06476b0db1b3/download/epd_202108.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202108.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/b98f8fe1-43ee-44ee-817d-f45ba3d179b8/download/epd_202109.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202109.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/ab642d37-f136-4c85-9708-9ed0486523bf/download/epd_202110.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202110.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/1ec38b44-395f-40ac-a8a9-81e661ef0a84/download/epd_202111.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202111.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/5f30033f-ecfa-4b78-a0df-5bba0aa59954/download/epd_202112.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202112.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/daf7515b-1176-4fb7-be02-1422819e6683/download/epd_202201.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202201.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/bbc61860-e866-45aa-b3d5-fc263d7bbe36/download/epd_202202.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202202.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/fc65d1c3-e6c1-432c-8809-ac4540a962fd/download/epd_202203.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202203.csv.gz

curl -L https://opendata.nhsbsa.net/dataset/65050ec0-5abd-48ce-989d-defc08ed837e/resource/af8dd944-fb82-42c1-a955-646c8866b939/download/epd_202204.csv \
| awk -v FS="\",\"" '{if($16 ~ /^0601/) {print $0}}' | gzip > source/prescriptions-BFD0601-202204.csv.gz
