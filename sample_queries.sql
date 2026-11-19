-- Shravani Kher, Kayla Hui
-- Final Project Phase I
-- Part (5) implementing representative sample of queries


-- query 4
WITH AllPoints AS (
  SELECT r.driverId, ra.year, r.points
  FROM results r
  JOIN races ra ON r.raceId = ra.raceId

  UNION ALL

  SELECT sr.driverId, ra.year, sr.points
  FROM sprint_results sr
  JOIN races ra ON sr.raceId = ra.raceId
),
SeasonPoints AS (
  SELECT driverId, year, SUM(points) AS totalPoints
  FROM AllPoints
  GROUP BY driverId, year
),
DriverAverages AS (
  SELECT driverId, year,totalPoints,
    AVG(totalPoints) OVER (PARTITION BY driverId) AS averagePoints
  FROM SeasonPoints
)
SELECT
  d.driverId,
  d.forename,
  d.surname,
  da.year,
  da.totalPoints,
  averagePoints
FROM DriverAverages da
JOIN drivers d ON da.driverId = d.driverId
WHERE da.totalPoints > da.averagePoints
ORDER BY d.driverId, da.year;


-- query 6
WITH AllPoints AS (
  SELECT r.constructorId, ra.raceId,
    ra.year, r.points
  FROM results r
  JOIN races ra ON r.raceId = ra.raceId

  UNION ALL

  SELECT sr.constructorId, ra.raceId,
    ra.year, sr.points
  FROM sprint_results sr
  JOIN races ra ON sr.raceId = ra.raceId
),
RacePoints AS (
  SELECT constructorId, raceId, year,
    SUM(points) AS racePoints
  FROM AllPoints
  GROUP BY constructorId, raceId, year
),
SeasonAverages AS (
  SELECT constructorId, year,
    AVG(racePoints) AS averagePoints
  FROM RacePoints
  GROUP BY constructorId, year
),
RankedConstructors AS (
  SELECT *,
    RANK() OVER (
      PARTITION BY year
      ORDER BY averagePoints DESC
    ) AS ranking
  FROM SeasonAverages
)
SELECT
  c.name AS constructorName,
  sa.year AS year,
  averagePoints
FROM RankedConstructors sa
JOIN constructors c
    ON sa.constructorId = c.constructorId
WHERE sa.ranking = 1
ORDER BY sa.year;


-- query 10
WITH CircuitRaceCounts AS (
  SELECT circuitId, COUNT(*) AS totalRaces
  FROM races
  GROUP BY circuitId
),
DriverWins AS (
  SELECT ra.circuitId, r.driverId,
    COUNT(*) AS totalWins
  FROM results r
  JOIN races ra ON r.raceId = ra.raceId
  WHERE r.position = 1
  GROUP BY ra.circuitId, r.driverId
),
RankedDrivers AS (
  SELECT *,
    RANK() OVER (
      PARTITION BY circuitId
      ORDER BY totalWins DESC
    ) AS ranking
  FROM DriverWins
)
SELECT
  ci.circuitId,
  ci.name AS circuitName,
  ci.country,
  crc.totalRaces,
  d.forename,
  d.surname,
  rd.totalWins
FROM RankedDrivers rd
JOIN circuits ci
  ON rd.circuitId = ci.circuitId
JOIN drivers d
  ON rd.driverId = d.driverId
JOIN CircuitRaceCounts crc
  ON rd.circuitId = crc.circuitId
WHERE rd.ranking = 1
ORDER BY ci.circuitId;


-- query 12
WITH GermanDriverStats AS (
  SELECT
    d.driverId,
    d.forename,
    d.surname,
    COUNT(*) AS totalRaces,
    AVG(r.position) AS averagePosition
  FROM drivers d
  JOIN results r ON d.driverId = r.driverId
  JOIN races ra ON r.raceId = ra.raceId
  JOIN circuits ci ON ra.circuitId = ci.circuitId
  WHERE ci.country = 'Germany'
  GROUP BY
    d.driverId,
    d.forename,
    d.surname
  HAVING COUNT(*) >= 5
),
RankedDrivers AS (
  SELECT *,
    RANK() OVER (
      ORDER BY averagePosition ASC
    ) AS ranking
  FROM GermanDriverStats
)
SELECT
  driverId,
  forename,
  surname,
  totalRaces,
  averagePosition
FROM RankedDrivers
WHERE ranking = 1 and r.position IS NOT NULL;


-- query 14
WITH CombinationStats AS (
  SELECT
    ra.circuitId,
    r.driverId,
    r.constructorId,
    COUNT(*) AS totalStarts,
    SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) AS totalWins,
    100.0 * SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) / COUNT(*) AS winPercentage
  FROM results r
  JOIN races ra ON r.raceId = ra.raceId
  GROUP BY
    ra.circuitId,
    r.driverId,
    r.constructorId
  HAVING COUNT(*) >= 5
),
RankedCombinations AS (
  SELECT *,
    RANK() OVER (
      PARTITION BY circuitId
      ORDER BY winPercentage DESC
    ) AS ranking
  FROM CombinationStats
)
SELECT
  d.forename,
  d.surname,
  c.name AS constructorName,
  ci.name AS circuitName,
  cs.totalStarts,
  cs.totalWins,
  winPercentage
FROM RankedCombinations cs
JOIN drivers d ON cs.driverId = d.driverId
JOIN constructors c ON cs.constructorId = c.constructorId
JOIN circuits ci ON cs.circuitId = ci.circuitId
WHERE cs.ranking = 1
ORDER BY ci.name;
