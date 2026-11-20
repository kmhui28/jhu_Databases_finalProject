--Create Tables correpsonding to each CSV!--

drop table IF EXISTS seasons;
CREATE TABLE seasons (
    year  INT PRIMARY KEY CHECK (year BETWEEN 1950 AND 2100),
    url   VARCHAR(255)
);

drop table IF EXISTS circuits;
CREATE TABLE circuits (
    circuitId   INT PRIMARY KEY,
    circuitRef  VARCHAR(50)  NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    location    VARCHAR(100),
    country     VARCHAR(60),
    lat         DECIMAL(9,6),
    lng         DECIMAL(9,6),
    alt         INT,
    url         VARCHAR(255)
);

drop table IF EXISTS constructors;
CREATE TABLE constructors (
    constructorId   INT PRIMARY KEY,
    constructorRef  VARCHAR(50)  NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    nationality     VARCHAR(50),
    url             VARCHAR(255)
);

drop table IF EXISTS drivers;
CREATE TABLE drivers (
    driverId    INT PRIMARY KEY,
    driverRef   VARCHAR(50)  NOT NULL UNIQUE,
    number      INT,                       
    code        CHAR(3),                  
    forename    VARCHAR(50)  NOT NULL,
    surname     VARCHAR(50)  NOT NULL,
    dob         DATE,
    nationality VARCHAR(50),
    url         VARCHAR(255)
);

drop table IF EXISTS status;
CREATE TABLE status (
    statusId  INT PRIMARY KEY,
    status    VARCHAR(50) NOT NULL       
);

drop table IF EXISTS races;
CREATE TABLE races (
    raceId     INT PRIMARY KEY,
    year       INT NOT NULL,
    round      INT NOT NULL CHECK (round >= 1),
    circuitId  INT NOT NULL,
    name       VARCHAR(100) NOT NULL,
    `date`     DATE NOT NULL,
    `time`     TIME,                      
    url        VARCHAR(255),
    UNIQUE (year, round),
    FOREIGN KEY (year)      REFERENCES seasons(year),
    FOREIGN KEY (circuitId) REFERENCES circuits(circuitId)
);

drop table IF EXISTS results;
CREATE TABLE results (
    resultId         INT PRIMARY KEY,
    raceId           INT NOT NULL,
    driverId         INT NOT NULL,
    constructorId    INT NOT NULL,
    number           INT,
    grid             INT NOT NULL CHECK (grid >= 0),      
    position         INT CHECK (position >= 1),           
    positionText     VARCHAR(5) NOT NULL,                 
    positionOrder    INT NOT NULL CHECK (positionOrder >= 1),
    points           DECIMAL(4,1) NOT NULL DEFAULT 0 CHECK (points >= 0),
    laps             INT NOT NULL CHECK (laps >= 0),
    `time`           VARCHAR(20),                         
    milliseconds     INT,
    fastestLap       INT,
    `rank`           INT,                                 
    fastestLapTime   VARCHAR(12),
    fastestLapSpeed  DECIMAL(7,3),
    statusId         INT NOT NULL,
    UNIQUE (raceId, driverId),
    FOREIGN KEY (raceId)        REFERENCES races(raceId),
    FOREIGN KEY (driverId)      REFERENCES drivers(driverId),
    FOREIGN KEY (constructorId) REFERENCES constructors(constructorId),
    FOREIGN KEY (statusId)      REFERENCES status(statusId)
);

drop table IF EXISTS sprint_results;
CREATE TABLE sprint_results (
    resultId         INT PRIMARY KEY,
    raceId           INT NOT NULL,
    driverId         INT NOT NULL,
    constructorId    INT NOT NULL,
    number           INT,
    grid             INT NOT NULL CHECK (grid >= 0),
    position         INT CHECK (position >= 1),
    positionText     VARCHAR(5) NOT NULL,
    positionOrder    INT NOT NULL CHECK (positionOrder >= 1),
    points           DECIMAL(4,1) NOT NULL DEFAULT 0 CHECK (points >= 0),
    laps             INT NOT NULL CHECK (laps >= 0),
    `time`           VARCHAR(20),
    milliseconds     INT,
    fastestLap       INT,
    fastestLapTime   VARCHAR(12),
    statusId         INT NOT NULL,
    FOREIGN KEY (raceId)        REFERENCES races(raceId),
    FOREIGN KEY (driverId)      REFERENCES drivers(driverId),
    FOREIGN KEY (constructorId) REFERENCES constructors(constructorId),
    FOREIGN KEY (statusId)      REFERENCES status(statusId)
);

drop table IF EXISTS qualifying;
CREATE TABLE qualifying (
    qualifyId      INT PRIMARY KEY,
    raceId         INT NOT NULL,
    driverId       INT NOT NULL,
    constructorId  INT NOT NULL,
    number         INT,
    position       INT NOT NULL CHECK (position >= 1),
    q1             VARCHAR(12),            
    q2             VARCHAR(12),
    q3             VARCHAR(12),
    UNIQUE (raceId, driverId),
    FOREIGN KEY (raceId)        REFERENCES races(raceId),
    FOREIGN KEY (driverId)      REFERENCES drivers(driverId),
    FOREIGN KEY (constructorId) REFERENCES constructors(constructorId)
);

drop table IF EXISTS lap_times;
CREATE TABLE lap_times (
    raceId        INT NOT NULL,
    driverId      INT NOT NULL,
    lap           INT NOT NULL CHECK (lap >= 1),
    position      INT,
    `time`        VARCHAR(12) NOT NULL,    
    milliseconds  INT NOT NULL CHECK (milliseconds > 0),
    PRIMARY KEY (raceId, driverId, lap),  
    FOREIGN KEY (raceId)   REFERENCES races(raceId),
    FOREIGN KEY (driverId) REFERENCES drivers(driverId)
);

drop table IF EXISTS pit_stops;
CREATE TABLE pit_stops (
    raceId        INT NOT NULL,
    driverId      INT NOT NULL,
    stop          INT NOT NULL CHECK (stop >= 1),
    lap           INT NOT NULL CHECK (lap >= 1),
    `time`        TIME NOT NULL,          
    duration      VARCHAR(12),             
    milliseconds  INT,
    PRIMARY KEY (raceId, driverId, stop),
    FOREIGN KEY (raceId)   REFERENCES races(raceId),
    FOREIGN KEY (driverId) REFERENCES drivers(driverId)
);

drop table IF EXISTS driver_standings;
CREATE TABLE driver_standings (
    driverStandingsId  INT PRIMARY KEY,
    raceId             INT NOT NULL,
    driverId           INT NOT NULL,
    points             DECIMAL(5,1) NOT NULL CHECK (points >= 0),
    position           INT NOT NULL CHECK (position >= 1),
    positionText       VARCHAR(5),
    wins               INT NOT NULL DEFAULT 0 CHECK (wins >= 0),
    UNIQUE (raceId, driverId),
    FOREIGN KEY (raceId)   REFERENCES races(raceId),
    FOREIGN KEY (driverId) REFERENCES drivers(driverId)
);

drop table IF EXISTS constructor_standings;
CREATE TABLE constructor_standings (
    constructorStandingsId  INT PRIMARY KEY,
    raceId                  INT NOT NULL,
    constructorId           INT NOT NULL,
    points                  DECIMAL(5,1) NOT NULL CHECK (points >= 0),
    position                INT NOT NULL CHECK (position >= 1),
    positionText            VARCHAR(5),
    wins                    INT NOT NULL DEFAULT 0 CHECK (wins >= 0),
    UNIQUE (raceId, constructorId),
    FOREIGN KEY (raceId)        REFERENCES races(raceId),
    FOREIGN KEY (constructorId) REFERENCES constructors(constructorId)
);

drop table IF EXISTS constructor_results;
CREATE TABLE constructor_results (
    constructorResultsId  INT PRIMARY KEY,
    raceId                INT NOT NULL,
    constructorId         INT NOT NULL,
    points                DECIMAL(4,1) NOT NULL DEFAULT 0 CHECK (points >= 0),
    status                VARCHAR(10),     
    FOREIGN KEY (raceId)        REFERENCES races(raceId),
    FOREIGN KEY (constructorId) REFERENCES constructors(constructorId)
);

DROP TABLE IF EXISTS circuit_details;

CREATE TABLE circuit_details (
    circuitId   INT NOT NULL,
    surface     VARCHAR(50),
    km          DECIMAL(5,3) NOT NULL CHECK (km > 0),
    turns       INT CHECK (turns > 0),
    yearOpen    INT NOT NULL CHECK (yearOpen BETWEEN 1900 AND 2100),
    yearClosed  INT,                          -- NULL = still in use
    raceRecord  VARCHAR(10)
                CHECK (raceRecord REGEXP '^[0-9]:[0-5][0-9][.][0-9]{3}$'),
    PRIMARY KEY (circuitId, yearOpen),
    CHECK (yearClosed IS NULL OR yearClosed >= yearOpen),
    FOREIGN KEY (circuitId) REFERENCES circuits(circuitId)
);
