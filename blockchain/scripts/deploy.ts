import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect("localhost");

  const repairChain = await ethers.deployContract("RepairChain");

  await repairChain.waitForDeployment();

  console.log("RepairChain deployed to:");
  console.log(await repairChain.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});