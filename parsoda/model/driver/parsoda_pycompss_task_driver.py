import math
import os
from collections import Callable
import queue
from typing import List, Optional
from parsoda.model.function.crawler import CrawlerPartition

from pycompss.api.task import task
from pycompss.dds import DDS
from pycompss.api.api import compss_barrier, compss_wait_on

from parsoda import SocialDataItem
from parsoda.model import ParsodaDriver, Crawler, Filter, Mapper, Reducer



@task(returns=list)
def _task_load_and_parse(partition: CrawlerPartition)->list:
    return partition.load_data().parse_data()

@task(returns=list)
def _task_parse(partition: CrawlerPartition)->list:
    return partition.parse_data()

@task(returns=list)
def _task_map(partition_mapper, partition: list)->list:
    return partition_mapper(partition)


def mapper_filter(filter_func, partition: list)->list:
    result = []
    for item in partition:
        if filter_func(item):
            result.append(item)
    return result


@task(returns=dict)
def _group_merge(part1: list, part2: list)->list:
    result = {}
    for part in [part1, part2]:
        for k, v in part:
            if k in result:
                result[k].append(v)
            else:
                result[k] = [v]
    return [(k,vs) for k, vs in result.items()]


@task(returns=list)
def _distribute_task(partition: list)->list:
    return partition

class ParsodaPyCompssTaskDriver(ParsodaDriver):
    """Parsoda driver for PyCOMPSs, based on PyCOMPSs task constructs. 
    
    This driver could be more efficient, depending on the installed version of PyCOMPSs, than its counterpart, the ParsodaPyCompssDriver, which is instead based on DDS.
    """

    def __init__(self):
        self.__chunk_size = None
        self.__num_partitions: Optional[int] = 8
        self.__partitions: Optional[List] = None
        self.__must_distribute = False
        
    def __map_partitions(self, partition_mapper):
        for i in range(len(self.__partitions)):
            self.__partitions[i] = _task_map(partition_mapper, self.__partitions[i])
    
    def __distribute(self):
        if len(self.__partitions) < self.__num_partitions:
            merged = self.__collect()
            
            new_partitions = []
            n = len(merged)
            k = len(self.__num_partitions)
            p_sizes = [n // k]*k
            reminder = n % k
            for i in range(reminder):
                p_sizes[i] += 1
            
            cursor = 0
            for p_size in p_sizes:
                end = cursor+p_size
                new_partitions.append(_distribute_task(merged[cursor:end]))
                cursor=end
            
            self.__partitions = new_partitions
            
    def __collect(self)->list:
        merged = []
        for p in self.__partitions:
            p = compss_wait_on(p)
            merged.extend(p)
        return merged
        
    def set_chunk_size(self, chunk_size: int):
        self.__chunk_size = chunk_size

    def set_num_partitions(self, num_partitions):
        self.__num_partitions = num_partitions

    def init_environment(self):
        self.__partitions = []*self.__num_partitions

    def dispose_environment(self):
        self.__partitions = None
    
    def crawl(self, crawlers: List[Crawler]):
        
        for crawler in crawlers:
            partitions: List[CrawlerPartition] = crawler.get_partitions(num_of_partitions=self.__num_partitions, partition_size=self.__chunk_size)
            if not crawler.supports_remote_partitioning():
                # master-located crawler, we must load partitions locally
                for p in partitions:
                    p.load_data()
                    p_data = _task_parse(p)
                    self.__partitions.append(p_data)
            else:
                # distributed crawler, we can load each data partition on a remote worker, in order to balance the reading workload
                for p in partitions:
                    p_data = _task_load_and_parse(p)
                    self.__partitions.append(p_data)
        #compss_barrier()

    def filter(self, filter_func):
        def mapper_filter(partition: list)->list:
            result = []
            for item in partition:
                if filter_func(item):
                    result.append(item)
            #print(f"filter result: {len(result)}")
            return result
        
        self.__map_partitions(mapper_filter)

    def flatmap(self, mapper):
        def mapper_flatmap(p):
            result = []
            for item in p:
                result.extend(mapper(item))
            return result
        
        self.__map_partitions(mapper_flatmap)

    def group_by_key(self) -> None:
        q = queue.Queue()
        for p in self.__partitions:
            q.put(p)
                    
        while q.qsize() > 1:
            p1 = q.get()
            p2 = q.get()
            merged = _group_merge(p1, p2)
            q.put(merged)
            
        self.__partitions = [q.get()]
        self.__distribute()
        
    def get_result(self):
        return self.__collect()
