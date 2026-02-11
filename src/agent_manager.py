"""
Parallel Agent Manager - Manages concurrent sub-agent execution for RLM
"""

import asyncio
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import time


@dataclass
class ChunkTask:
    """Task for processing a chunk"""
    id: int
    content: Any
    task_type: str = "extraction"
    query: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Result:
    """Result from chunk processing"""
    chunk_id: int
    content: Any
    processing_time_ms: float
    model_used: str = "haiku"
    error: Optional[str] = None


class ParallelAgentManager:
    """Manages parallel execution of RLM sub-agents"""
    
    def __init__(self, max_concurrent: int = 8, llm_query_fn: Optional[Callable] = None):
        self.max_concurrent = max_concurrent
        self.llm_query_fn = llm_query_fn
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent)
        self._active_tasks = {}
        self._completed_results = []
    
    def process_chunks_sync(self, chunks: List[Dict], query: str) -> List[Result]:
        """Process chunks synchronously with parallel execution"""
        chunk_tasks = [
            ChunkTask(
                id=i,
                content=chunk.get('content', chunk),
                task_type="query",
                query=query,
                metadata=chunk if isinstance(chunk, dict) else {}
            )
            for i, chunk in enumerate(chunks)
        ]
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = [
                executor.submit(self._process_single_chunk, task)
                for task in chunk_tasks
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    results.append(Result(
                        chunk_id=-1,
                        content=None,
                        processing_time_ms=0,
                        error=str(e)
                    ))
        
        results.sort(key=lambda r: r.chunk_id)
        return results
    
    async def process_chunks_async(self, chunks: List[Dict], query: str) -> List[Result]:
        """Process chunks asynchronously"""
        chunk_tasks = [
            ChunkTask(
                id=i,
                content=chunk.get('content', chunk),
                task_type="query",
                query=query,
                metadata=chunk if isinstance(chunk, dict) else {}
            )
            for i, chunk in enumerate(chunks)
        ]
        
        tasks = []
        for batch in self._batch_tasks(chunk_tasks, self.max_concurrent):
            batch_tasks = [
                asyncio.create_task(self._process_chunk_async(task))
                for task in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    tasks.append(Result(
                        chunk_id=-1,
                        content=None,
                        processing_time_ms=0,
                        error=str(result)
                    ))
                else:
                    tasks.append(result)
        
        return tasks
    
    def _process_single_chunk(self, task: ChunkTask) -> Result:
        """Process a single chunk"""
        start_time = time.time()
        
        try:
            if not self.llm_query_fn:
                content = f"[Processed chunk {task.id}: {len(str(task.content))} chars]"
            else:
                model = self._select_model(task)
                prompt = self._build_prompt(task)
                content = self.llm_query_fn(prompt, model=model)
            
            processing_time = (time.time() - start_time) * 1000
            
            return Result(
                chunk_id=task.id,
                content=content,
                processing_time_ms=processing_time,
                model_used=self._select_model(task)
            )
        except Exception as e:
            return Result(
                chunk_id=task.id,
                content=None,
                processing_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _process_chunk_async(self, task: ChunkTask) -> Result:
        """Process chunk asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._process_single_chunk, task)
    
    def _select_model(self, task: ChunkTask) -> str:
        """Select appropriate model based on task type"""
        if task.task_type == "extraction":
            return "haiku"
        elif task.task_type == "analysis":
            return "sonnet"
        elif task.task_type == "synthesis":
            return "sonnet"
        else:
            return "haiku"
    
    def _build_prompt(self, task: ChunkTask) -> str:
        """Build prompt for chunk processing"""
        if task.query:
            return f"""Process this chunk of data to answer the following query:

Query: {task.query}

Chunk {task.id}:
{str(task.content)[:10000]}

Provide a concise response focusing only on information relevant to the query."""
        else:
            return f"""Extract key information from this chunk:

Chunk {task.id}:
{str(task.content)[:10000]}

Provide a structured summary of the main points."""
    
    def _batch_tasks(self, tasks: List[ChunkTask], batch_size: int) -> List[List[ChunkTask]]:
        """Batch tasks for parallel processing"""
        batches = []
        for i in range(0, len(tasks), batch_size):
            batches.append(tasks[i:i+batch_size])
        return batches
    
    def aggregate_results(self, results: List[Result]) -> Dict[str, Any]:
        """Aggregate results from multiple chunks"""
        successful = [r for r in results if r.error is None]
        failed = [r for r in results if r.error is not None]
        
        total_time = sum(r.processing_time_ms for r in results)
        
        if all(isinstance(r.content, str) for r in successful):
            aggregated_content = '\n\n'.join(
                f"[Chunk {r.chunk_id}]:\n{r.content}"
                for r in successful
            )
        elif all(isinstance(r.content, dict) for r in successful):
            aggregated_content = {}
            for r in successful:
                if isinstance(r.content, dict):
                    aggregated_content.update(r.content)
        else:
            aggregated_content = [r.content for r in successful]
        
        return {
            "aggregated": aggregated_content,
            "chunks_processed": len(successful),
            "chunks_failed": len(failed),
            "total_processing_time_ms": total_time,
            "errors": [{"chunk": r.chunk_id, "error": r.error} for r in failed]
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self._executor.shutdown(wait=False)