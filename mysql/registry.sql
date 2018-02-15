-- MySQL dump 10.13  Distrib 5.7.20, for Win64 (x86_64)
--
-- Host: localhost    Database: registry
-- ------------------------------------------------------
-- Server version	5.7.20-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `repositories`
--

CREATE DATABASE registry;
USE registry;

DROP TABLE IF EXISTS `repositories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `repositories` (
  `id_` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) DEFAULT NULL,
  `description` varchar(500) DEFAULT NULL,
  `downloads` int(11) DEFAULT NULL,
  `uri` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id_`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `uri` (`uri`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `repositories`
--

LOCK TABLES `repositories` WRITE;
/*!40000 ALTER TABLE `repositories` DISABLE KEYS */;
INSERT INTO `repositories` VALUES (1,'usd_dev:anim','Production version of USD in Docker for feature animation pipeline.',0,'usd_dev.anim'),(2,'usd_dev:v2','Second version of USD in Docker development.',0,'usd_dev.v2'),(3,'alembic-base','The base of alembic caches.',0,'alembic-base.v1'),(4,'nodes editor','Generic Qt Node editor.',0,'nodes_editor.v1'),(5,'usd_s','Standalone USD workflow.',0,'usd_standalone.v2');
/*!40000 ALTER TABLE `repositories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `repositories_tags`
--

DROP TABLE IF EXISTS `repositories_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `repositories_tags` (
  `tag_id` int(11) DEFAULT NULL,
  `repo_id` int(11) DEFAULT NULL,
  KEY `tag_id` (`tag_id`),
  KEY `repo_id` (`repo_id`),
  CONSTRAINT `repositories_tags_ibfk_1` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id_`),
  CONSTRAINT `repositories_tags_ibfk_2` FOREIGN KEY (`repo_id`) REFERENCES `repositories` (`id_`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `repositories_tags`
--

LOCK TABLES `repositories_tags` WRITE;
/*!40000 ALTER TABLE `repositories_tags` DISABLE KEYS */;
INSERT INTO `repositories_tags` VALUES (1,1),(1,2),(2,2),(3,3),(2,3),(4,4),(2,4),(5,5);
/*!40000 ALTER TABLE `repositories_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tags`
--

DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tags` (
  `id_` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `popularity` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tags`
--

LOCK TABLES `tags` WRITE;
/*!40000 ALTER TABLE `tags` DISABLE KEYS */;
INSERT INTO `tags` VALUES (1,'docker usd',1),(2,'\"vfx pipeline\"',1),(3,'\"alembic file format\"',2),(4,'node graph qt',2),(5,'z',1);
/*!40000 ALTER TABLE `tags` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-02-14 23:36:43
