HELM_VER=`curl -s https://api.github.com/repos/helm/helm/releases/latest | grep tag_name | cut -d: -f2 | tr -d \"\,\v | awk '{$1=$1};1'`
wget https://get.helm.sh/helm-v${HELM_VER}-linux-arm64.tar.gz
tar -zxvf helm-v${HELM_VER}-linux-arm64.tar.gz
sudo cp linux-arm64/helm /usr/local/bin/