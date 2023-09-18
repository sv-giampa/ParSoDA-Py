from datetime import date
import sys
import argparse

from parsoda import SocialDataApp
from parsoda.apps.trajectory_mining import parsoda_trajectory_mining
from parsoda.function.analysis.gap_bide_analysis import GapBIDE
from parsoda.function.crawling.distributed_file_crawler import DistributedFileCrawler
from parsoda.function.crawling.local_file_crawler import LocalFileCrawler
from parsoda.function.crawling.parsing.flickr_parser import FlickrParser
from parsoda.function.crawling.parsing.parsoda_parser import ParsodaParser
from parsoda.function.crawling.parsing.twitter_parser import TwitterParser
from parsoda.function.crawling.parsing.vinitaly2019_parser import Vinitaly2019Parser
from parsoda.function.filtering import IsInPlace, IsInRoI

from parsoda.function.mapping.find_poi import FindPoI
from parsoda.function.reduction.reduce_by_trajectories import ReduceByTrajectories
from parsoda.function.visualization.sort_gap_bide import SortGapBIDE
from parsoda.utils.roi import RoI



def parse_command_line():
    def type_driver(arg: str) -> ParsodaDriver:
        if arg == "pycompss": 
            from parsoda.model.driver.parsoda_pycompss_driver import ParsodaPyCompssDriver
            return ParsodaPyCompssDriver()
        elif arg == "pyspark":
            from parsoda.model.driver.parsoda_pyspark_driver import ParsodaPySparkDriver
            import pyspark
            return ParsodaPySparkDriver(pyspark.SparkContext(conf=pyspark.SparkConf()))
        elif arg == "singlecore":
            from parsoda.model.driver.parsoda_singlecore_driver import ParsodaSingleCoreDriver
            return ParsodaSingleCoreDriver()
        else:
            raise Exception(f"Undefined driver \"{arg}\"")
            
    
    parser = argparse.ArgumentParser(description='Trajectory Mining application on top of PyCOMPSs')
    
    parser.add_argument(
        "driver",
        type=type_driver,
        help="ParSoDA driver to use. It can be: 'pycompss', 'pyspark' or 'singlecore'"
    )
    parser.add_argument(
        "--partitions", "-p",
        type=int,
        default=-1,
        help="specifies the number of data partitions."
    )
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=128,
        help="specifies the size of data partitions in megabytes."
    )
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_command_line()
    
    app = parsoda_trajectory_mining(
        driver = args.driver
        crawlers = [
            #DistributedFileCrawler('/storage/dataset/TwitterRome2017_6X.json', TwitterParser())
            DistributedFileCrawler('resources/input/synthetic_40m.json', ParsodaParser())
        ],
        rois_file="./resources/input/RomeRoIs.kml",
        num_partitions=args.partitions, 
        chunk_size=args.chunk_size
    )
    app.execute()
    
