For Testing Build

# For Fast api server
docker build . --target api_test -t trade-core:test 
# For trade core
docker buld . --target test -t trade-core:test 
