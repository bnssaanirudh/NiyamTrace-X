$ErrorActionPreference = "Stop"
$Repo = "https://github.com/bnssaanirudh/NiyamTrace-X.git"
$Commit = "c14661dbd11c42ebd1019b6a1a5c49b8643da137"
git clone $Repo NiyamTrace-X-public
Set-Location NiyamTrace-X-public
git checkout $Commit
git rev-parse HEAD
