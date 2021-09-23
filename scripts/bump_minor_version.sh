#!/usr/bin/bash
current_project=$1 # project name under ./src

# can bump the most minor version for any string
# VERSIONS="
# 1.2.3.4.4
# 1.2.3.4.5.6.7.7
# 1.9.9
# 1.9.0.9
# "
product=$1

function get_product_version {
	grep '__version__ =' src/$current_project/$current_project/__init__.py | cut -d' ' -f3 | xargs
}

current_version=$(get_product_version)
bumped_version=$(echo $current_version | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')

sed -i bak -e "s|${current_version}|${bumped_version}|g"  "src/${current_project}/${current_project}/__init__.py"
