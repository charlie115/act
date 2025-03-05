For Testing Build

# For Fast api server
docker build . --target api_test -t trade-core-api:test 
# For trade core
docker build . --target test -t trade-core:test 
