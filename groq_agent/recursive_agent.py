"""Recursive Agent System - Breaks down goals and maintains context across multiple goals."""

import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .config import ConfigurationManager
from .api_client import GroqAPIClient
from .handbook_manager import HandbookManager, ChangeRecord
from .agentic_system import AgenticSystem


class GoalStatus(Enum):
    """Status of a goal."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SubGoal:
    """A sub-goal within a larger goal."""
    id: str
    description: str
    status: GoalStatus
    dependencies: List[str] = field(default_factory=list)
    files_to_modify: List[str] = field(default_factory=list)
    expected_changes: Dict[str, Any] = field(default_factory=dict)
    context_from_previous: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class Goal:
    """A goal that can be broken down into sub-goals."""
    id: str
    description: str
    user_prompt: str
    status: GoalStatus
    sub_goals: List[SubGoal] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    files_changed: List[str] = field(default_factory=list)
    changes_made: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    priority: int = 1  # 1 = highest, 5 = lowest


class RecursiveAgent:
    """Recursive agent that breaks down goals and maintains context across multiple goals."""
    
    def __init__(self, config: ConfigurationManager, api_client: GroqAPIClient, 
                 handbook_manager: HandbookManager, agentic_system: AgenticSystem):
        """Initialize the recursive agent.
        
        Args:
            config: Configuration manager instance
            api_client: Groq API client instance
            handbook_manager: Handbook manager instance
            agentic_system: Agentic system instance
        """
        self.config = config
        self.api_client = api_client
        self.handbook_manager = handbook_manager
        self.agentic_system = agentic_system
        
        # Goal tracking
        self.current_goal: Optional[Goal] = None
        self.goal_history: List[Goal] = []
        self.context_chain: List[Dict[str, Any]] = []
        
        # Agent state
        self.is_executing = False
        self.max_sub_goals = 10  # Maximum sub-goals per goal
        self.context_window_size = 5  # Number of previous contexts to keep
    
    def execute_goal(self, user_prompt: str, goal_description: str) -> Dict[str, Any]:
        """Execute a goal by breaking it down into sub-goals and executing them recursively.
        
        Args:
            user_prompt: The original user prompt
            goal_description: Description of what needs to be accomplished
            
        Returns:
            Dictionary containing execution results
        """
        # Create the main goal
        goal_id = f"goal_{int(time.time())}"
        self.current_goal = Goal(
            id=goal_id,
            description=goal_description,
            user_prompt=user_prompt,
            status=GoalStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            # Step 1: Break down the goal into sub-goals
            self._break_down_goal()
            
            # Step 2: Execute sub-goals in order
            self._execute_sub_goals()
            
            # Step 3: Finalize the goal
            self._finalize_goal()
            
            return {
                'success': True,
                'goal_id': goal_id,
                'sub_goals_completed': len([sg for sg in self.current_goal.sub_goals if sg.status == GoalStatus.COMPLETED]),
                'files_changed': self.current_goal.files_changed,
                'changes_made': self.current_goal.changes_made
            }
            
        except Exception as e:
            self.current_goal.status = GoalStatus.FAILED
            self.current_goal.end_time = datetime.now()
            return {
                'success': False,
                'error': str(e),
                'goal_id': goal_id
            }
        finally:
            # Add to history
            self.goal_history.append(self.current_goal)
            self.current_goal = None
    
    def _break_down_goal(self) -> None:
        """Break down the main goal into sub-goals."""
        if not self.current_goal:
            raise ValueError("No current goal to break down")
        
        # Get context from handbook
        context = self.handbook_manager.get_context_for_goal(self.current_goal.description)
        
        # Use AI to break down the goal
        breakdown_prompt = self._create_breakdown_prompt()
        breakdown_response = self._get_ai_breakdown(breakdown_prompt, context)
        
        # Parse the breakdown into sub-goals
        sub_goals = self._parse_breakdown_response(breakdown_response)
        
        # Add sub-goals to the current goal
        self.current_goal.sub_goals = sub_goals
        self.current_goal.status = GoalStatus.IN_PROGRESS
    
    def _create_breakdown_prompt(self) -> str:
        """Create a prompt for breaking down the goal."""
        return f"""
You are a goal breakdown specialist. Your task is to break down the following user goal into 3-5 specific, actionable sub-goals.

User Goal: {self.current_goal.description}
User Prompt: {self.current_goal.user_prompt}

Please break this down into sub-goals that:
1. Are specific and actionable
2. Can be executed in sequence
3. Each sub-goal builds on the context from previous sub-goals
4. Are focused on specific files or functions that need to be modified

For each sub-goal, provide:
- A clear description
- Which files need to be modified
- What specific changes are expected
- Any dependencies on previous sub-goals

Format your response as JSON:
{{
    "sub_goals": [
        {{
            "description": "Sub-goal description",
            "files_to_modify": ["file1.py", "file2.py"],
            "expected_changes": {{
                "file1.py": "What changes to make",
                "file2.py": "What changes to make"
            }},
            "dependencies": []
        }}
    ]
}}
"""
    
    def _get_ai_breakdown(self, prompt: str, context: Dict[str, Any]) -> str:
        """Get AI breakdown of the goal."""
        # Use the agentic system to get AI response
        try:
            # Create a tool call for AI analysis
            from .agentic_system import ToolCall, ToolType
            
            tool_call = ToolCall(
                tool_name="ai_breakdown",
                tool_type=ToolType.ANALYZE,
                parameters={
                    'prompt': prompt,
                    'context': context
                }
            )
            
            # For now, return a mock breakdown
            # In a real implementation, this would use the AI model
            return self._get_mock_breakdown()
            
        except Exception as e:
            # Fallback to mock breakdown
            return self._get_mock_breakdown()
    
    def _get_mock_breakdown(self) -> str:
        """Get a mock breakdown for testing."""
        return json.dumps({
            "sub_goals": [
                {
                    "description": "Analyze current codebase structure and identify files to modify",
                    "files_to_modify": [],
                    "expected_changes": {},
                    "dependencies": []
                },
                {
                    "description": "Implement the core functionality changes",
                    "files_to_modify": ["groq_agent/agentic_system.py"],
                    "expected_changes": {
                        "groq_agent/agentic_system.py": "Add new functionality"
                    },
                    "dependencies": [0]
                },
                {
                    "description": "Update documentation and handbook",
                    "files_to_modify": ["CodeFlowNinjaHandbook.md"],
                    "expected_changes": {
                        "CodeFlowNinjaHandbook.md": "Update with new changes"
                    },
                    "dependencies": [1]
                }
            ]
        })
    
    def _parse_breakdown_response(self, response: str) -> List[SubGoal]:
        """Parse the AI breakdown response into SubGoal objects."""
        try:
            data = json.loads(response)
            sub_goals = []
            
            for i, sg_data in enumerate(data.get('sub_goals', [])):
                sub_goal = SubGoal(
                    id=f"{self.current_goal.id}_sub_{i}",
                    description=sg_data.get('description', ''),
                    status=GoalStatus.PENDING,
                    dependencies=sg_data.get('dependencies', []),
                    files_to_modify=sg_data.get('files_to_modify', []),
                    expected_changes=sg_data.get('expected_changes', {})
                )
                sub_goals.append(sub_goal)
            
            return sub_goals
            
        except Exception as e:
            # Fallback to basic sub-goals
            return [
                SubGoal(
                    id=f"{self.current_goal.id}_sub_0",
                    description="Execute the main goal",
                    status=GoalStatus.PENDING,
                    files_to_modify=[],
                    expected_changes={}
                )
            ]
    
    def _execute_sub_goals(self) -> None:
        """Execute sub-goals in order, passing context between them."""
        if not self.current_goal or not self.current_goal.sub_goals:
            return
        
        for i, sub_goal in enumerate(self.current_goal.sub_goals):
            try:
                # Check dependencies
                if not self._check_dependencies(sub_goal):
                    sub_goal.status = GoalStatus.BLOCKED
                    continue
                
                # Execute the sub-goal
                self._execute_single_sub_goal(sub_goal, i)
                
                # Update context chain
                self._update_context_chain(sub_goal)
                
            except Exception as e:
                sub_goal.status = GoalStatus.FAILED
                sub_goal.error_message = str(e)
                sub_goal.end_time = datetime.now()
    
    def _check_dependencies(self, sub_goal: SubGoal) -> bool:
        """Check if all dependencies for a sub-goal are satisfied."""
        for dep_id in sub_goal.dependencies:
            dep_index = int(dep_id)
            if dep_index >= len(self.current_goal.sub_goals):
                return False
            
            dep_sub_goal = self.current_goal.sub_goals[dep_index]
            if dep_sub_goal.status != GoalStatus.COMPLETED:
                return False
        
        return True
    
    def _execute_single_sub_goal(self, sub_goal: SubGoal, index: int) -> None:
        """Execute a single sub-goal."""
        sub_goal.status = GoalStatus.IN_PROGRESS
        sub_goal.start_time = datetime.now()
        
        # Get context from previous sub-goals
        context = self._get_context_for_sub_goal(sub_goal, index)
        sub_goal.context_from_previous = context
        
        # Execute the sub-goal using the agentic system
        result = self._execute_sub_goal_with_agentic_system(sub_goal, context)
        
        # Update sub-goal with results
        sub_goal.result = result
        sub_goal.status = GoalStatus.COMPLETED
        sub_goal.end_time = datetime.now()
        
        # Update main goal with changes
        if result.get('files_changed'):
            self.current_goal.files_changed.extend(result['files_changed'])
        if result.get('changes_made'):
            self.current_goal.changes_made.extend(result['changes_made'])
    
    def _get_context_for_sub_goal(self, sub_goal: SubGoal, index: int) -> Dict[str, Any]:
        """Get context for a sub-goal from previous sub-goals."""
        context = {
            'handbook_data': self.handbook_manager.handbook_data,
            'previous_results': {},
            'files_changed': [],
            'changes_made': []
        }
        
        # Get results from dependent sub-goals
        for dep_id in sub_goal.dependencies:
            dep_index = int(dep_id)
            if dep_index < len(self.current_goal.sub_goals):
                dep_sub_goal = self.current_goal.sub_goals[dep_index]
                if dep_sub_goal.result:
                    context['previous_results'][dep_id] = dep_sub_goal.result
        
        # Get context from context chain
        if self.context_chain:
            context['context_chain'] = self.context_chain[-self.context_window_size:]
        
        return context
    
    def _execute_sub_goal_with_agentic_system(self, sub_goal: SubGoal, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sub-goal using the agentic system."""
        # Use the agentic system's execute_sub_goal method
        result = self.agentic_system.execute_sub_goal(
            sub_goal_description=sub_goal.description,
            files_to_modify=sub_goal.files_to_modify,
            expected_changes=sub_goal.expected_changes,
            context=context
        )
        
        return result
    
    def _create_sub_goal_prompt(self, sub_goal: SubGoal, context: Dict[str, Any]) -> str:
        """Create a prompt for executing a sub-goal."""
        return f"""
Execute the following sub-goal:

Sub-goal: {sub_goal.description}
Files to modify: {', '.join(sub_goal.files_to_modify)}
Expected changes: {json.dumps(sub_goal.expected_changes, indent=2)}

Context from previous sub-goals:
{json.dumps(context.get('previous_results', {}), indent=2)}

Please execute this sub-goal by:
1. Analyzing the current state of the files
2. Making the necessary changes
3. Ensuring changes are minimal and focused
4. Updating the handbook with the changes made

Focus only on the specific changes needed for this sub-goal.
"""
    
    def _update_context_chain(self, sub_goal: SubGoal) -> None:
        """Update the context chain with results from a sub-goal."""
        context_entry = {
            'timestamp': datetime.now().isoformat(),
            'sub_goal_id': sub_goal.id,
            'description': sub_goal.description,
            'result': sub_goal.result,
            'files_changed': sub_goal.files_to_modify,
            'context_passed': sub_goal.context_from_previous
        }
        
        self.context_chain.append(context_entry)
        
        # Keep only the last N entries
        if len(self.context_chain) > self.context_window_size:
            self.context_chain = self.context_chain[-self.context_window_size:]
    
    def _finalize_goal(self) -> None:
        """Finalize the goal and update the handbook."""
        if not self.current_goal:
            return
        
        self.current_goal.status = GoalStatus.COMPLETED
        self.current_goal.end_time = datetime.now()
        
        # Create a change record
        change_record = ChangeRecord(
            timestamp=datetime.now().isoformat(),
            goal=self.current_goal.description,
            files_changed=self.current_goal.files_changed,
            changes_description=f"Completed goal: {self.current_goal.description}",
            impact_analysis="Goal completed successfully",
            context_passed={
                'sub_goals_completed': len([sg for sg in self.current_goal.sub_goals if sg.status == GoalStatus.COMPLETED]),
                'total_sub_goals': len(self.current_goal.sub_goals),
                'context_chain_length': len(self.context_chain)
            }
        )
        
        # Add to handbook
        self.handbook_manager.add_change_record(change_record)
    
    def get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific goal."""
        for goal in self.goal_history:
            if goal.id == goal_id:
                return {
                    'id': goal.id,
                    'description': goal.description,
                    'status': goal.status.value,
                    'sub_goals': [
                        {
                            'id': sg.id,
                            'description': sg.description,
                            'status': sg.status.value,
                            'result': sg.result
                        }
                        for sg in goal.sub_goals
                    ],
                    'files_changed': goal.files_changed,
                    'start_time': goal.start_time.isoformat() if goal.start_time else None,
                    'end_time': goal.end_time.isoformat() if goal.end_time else None
                }
        
        return None
    
    def get_recent_goals(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent goals."""
        recent_goals = []
        for goal in self.goal_history[-limit:]:
            recent_goals.append({
                'id': goal.id,
                'description': goal.description,
                'status': goal.status.value,
                'start_time': goal.start_time.isoformat() if goal.start_time else None
            })
        
        return recent_goals
