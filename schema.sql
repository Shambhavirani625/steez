PRAGMA FOREIGN_KEYS = ON;
PRAGMA JOURNAL_MODE = WAL;
PRAGMA SYNCHRONOUS = 1;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS `USERS` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `EMAIL`     VARCHAR(255)    UNIQUE          NOT NULL,
    `PASSWORD`  CHAR(64)        NOT NULL,
    `NAME`      VARCHAR(255)    NOT NULL,
    `ROLE`      CHAR(5)         DEFAULT        'USER',
    `ADDRESS`   TEXT            NOT NULL,
    `PHONE`     CHAR(10)        NOT NULL,

    `CREATED_AT` TIMESTAMP      DEFAULT         CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PRODUCTS` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `NAME`      VARCHAR(255)    NOT NULL,
    `PRICE`     DECIMAL(10, 2)  NOT NULL,
    `DESCRIPTION` TEXT          NOT NULL,
    `STOCK`     INTEGER         DEFAULT         -1
);

CREATE TABLE IF NOT EXISTS `CARTS` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `USER_ID`   INTEGER         NOT NULL,
    `PRODUCT_ID` INTEGER        NOT NULL,
    `QUANTITY`  INTEGER         NOT NULL,

    FOREIGN KEY (`USER_ID`)     REFERENCES `USERS`(`ID`)    ON DELETE CASCADE,
    FOREIGN KEY (`PRODUCT_ID`)  REFERENCES `PRODUCTS`(`ID`) ON DELETE CASCADE,

    CONSTRAINT `UNIQUE_CART`    UNIQUE (`USER_ID`, `PRODUCT_ID`)
);

CREATE TABLE IF NOT EXISTS `ORDERS` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `USER_ID`   INTEGER         NOT NULL,
    `PRODUCT_ID` INTEGER        NOT NULL,
    `QUANTITY`  INTEGER         NOT NULL,
    `TOTAL_PRICE` DECIMAL(10, 2) NOT NULL,
    `CREATED_AT` TIMESTAMP      DEFAULT         CURRENT_TIMESTAMP,
    `STATUS`    CHAR(4)         DEFAULT         'PEND',
    `RAZORPAY_ORDER_ID` TEXT    DEFAULT         NULL,

    FOREIGN KEY (`USER_ID`)     REFERENCES `USERS`(`ID`)    ON DELETE CASCADE,
    FOREIGN KEY (`PRODUCT_ID`)  REFERENCES `PRODUCTS`(`ID`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `REVIEWS` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `USER_ID`   INTEGER         NOT NULL,
    `PRODUCT_ID` INTEGER        NOT NULL,
    `STARS`     INTEGER         NOT NULL,
    `REVIEW`    VARCHAR(255)    NOT NULL,
    `CREATED_AT` TIMESTAMP      DEFAULT         CURRENT_TIMESTAMP,

    FOREIGN KEY (`USER_ID`)     REFERENCES `USERS`(`ID`)    ON DELETE CASCADE,
    FOREIGN KEY (`PRODUCT_ID`)  REFERENCES `PRODUCTS`(`ID`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `FAVOURITES` (
    `ID`        INTEGER         PRIMARY KEY     AUTOINCREMENT,
    `USER_ID`   INTEGER         NOT NULL,
    `PRODUCT_ID` INTEGER        NOT NULL,

    FOREIGN KEY (`USER_ID`)     REFERENCES `USERS`(`ID`)    ON DELETE CASCADE,
    FOREIGN KEY (`PRODUCT_ID`)  REFERENCES `PRODUCTS`(`ID`) ON DELETE CASCADE,

    CONSTRAINT `UNIQUE_FAVORITE` UNIQUE (`USER_ID`, `PRODUCT_ID`) ON CONFLICT REPLACE
);

COMMIT;
