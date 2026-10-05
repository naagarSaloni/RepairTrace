// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RepairChain {

    struct RepairRecord {
        string repairId;
        string recordHash;
        uint256 timestamp;
        address recordedBy;
    }

    mapping(string => RepairRecord) private repairRecords;

    event RepairRecorded(
        string indexed repairId,
        string recordHash,
        uint256 timestamp,
        address recordedBy
    );

    function addRepairRecord(
        string memory _repairId,
        string memory _recordHash
    ) public {
        require(bytes(_repairId).length > 0, "Repair ID is required");
        require(bytes(_recordHash).length > 0, "Record hash is required");
        require(
            bytes(repairRecords[_repairId].recordHash).length == 0,
            "Repair record already exists"
        );

        repairRecords[_repairId] = RepairRecord({
            repairId: _repairId,
            recordHash: _recordHash,
            timestamp: block.timestamp,
            recordedBy: msg.sender
        });

        emit RepairRecorded(
            _repairId,
            _recordHash,
            block.timestamp,
            msg.sender
        );
    }

    function getRepairRecord(
        string memory _repairId
    )
        public
        view
        returns (
            string memory repairId,
            string memory recordHash,
            uint256 timestamp,
            address recordedBy
        )
    {
        RepairRecord memory record = repairRecords[_repairId];

        require(
            bytes(record.recordHash).length > 0,
            "Repair record not found"
        );

        return (
            record.repairId,
            record.recordHash,
            record.timestamp,
            record.recordedBy
        );
    }

    function verifyRepair(
        string memory _repairId,
        string memory _recordHash
    ) public view returns (bool) {
        RepairRecord memory record = repairRecords[_repairId];

        return keccak256(bytes(record.recordHash)) ==
               keccak256(bytes(_recordHash));
    }
}