import { expect } from "chai";
import { network } from "hardhat";

describe("RepairChain", function () {
  async function deployRepairChain() {
    const { ethers } = await network.connect();

    const repairChain = await ethers.deployContract("RepairChain");

    await repairChain.waitForDeployment();

    return repairChain;
  }

  it("Should store and retrieve a repair record", async function () {
    const repairChain = await deployRepairChain();

    const repairId = "REP-9E8512167D";
    const recordHash =
      "221c649360e32c2bb3088490733b104e874bf34b5310a6314c49f1ad98c3907f";

    await repairChain.addRepairRecord(
      repairId,
      recordHash
    );

    const record =
      await repairChain.getRepairRecord(repairId);

    expect(record[0]).to.equal(repairId);
    expect(record[1]).to.equal(recordHash);
  });

  it("Should verify a correct repair hash", async function () {
    const repairChain = await deployRepairChain();

    const repairId = "REP-TEST-001";
    const recordHash =
      "221c649360e32c2bb3088490733b104e874bf34b5310a6314c49f1ad98c3907f";

    await repairChain.addRepairRecord(
      repairId,
      recordHash
    );

    const result =
      await repairChain.verifyRepair(
        repairId,
        recordHash
      );

    expect(result).to.equal(true);
  });

  it("Should reject an incorrect repair hash", async function () {
    const repairChain = await deployRepairChain();

    const repairId = "REP-TEST-002";

    const originalHash =
      "221c649360e32c2bb3088490733b104e874bf34b5310a6314c49f1ad98c3907f";

    const wrongHash =
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

    await repairChain.addRepairRecord(
      repairId,
      originalHash
    );

    const result =
      await repairChain.verifyRepair(
        repairId,
        wrongHash
      );

    expect(result).to.equal(false);
  });
});