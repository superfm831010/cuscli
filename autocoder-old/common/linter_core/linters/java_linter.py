"""
Java linter implementation using javac for syntax checking with dependency support.

Supports Maven, Gradle, and local JAR dependencies for accurate type checking.
"""

from __future__ import annotations

import os
import subprocess
import time
import tempfile
import json
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path
from functools import lru_cache

from ..base_linter import BaseLinter
from ..models.lint_result import LintResult


class JavaLinter(BaseLinter):
    """Java linter using javac with support for project dependencies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.javac_args: List[str] = self.get_config_value('javac_args', [])
        self.javac_timeout_secs: int = self.get_config_value('javac_timeout', 30)
        
        # Dependency resolution configuration
        self.project_type: str = self.get_config_value('project_type', 'auto')  # auto/maven/gradle/local
        self.source_paths: List[str] = self.get_config_value('source_paths', ['src', 'src/main/java'])
        self.lib_dirs: List[str] = self.get_config_value('lib_dirs', ['lib', 'libs'])
        self.enable_dependency_resolution: bool = self.get_config_value('enable_dependency_resolution', True)
        self.cache_dependencies: bool = self.get_config_value('cache_dependencies', True)
        self.release_version: str = self.get_config_value('release', '8')  # Default to Java 8
        self.use_release_flag: bool = self.get_config_value('use_release_flag', True)  # Can be disabled for older javac
        
        # Cache for resolved dependencies
        self._classpath_cache: Optional[str] = None
        self._project_root_cache: Optional[Path] = None

    @property
    def supported_extensions(self) -> List[str]:
        return ['.java']

    @property
    def language_name(self) -> str:
        return "Java"

    def is_available(self) -> bool:
        try:
            subprocess.run(['javac', '-version'], capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def lint_file(self, file_path: Union[str, Path]) -> LintResult:
        start_time = time.time()
        path = Path(file_path)
        result = LintResult(
            linter_name=self.name,
            files_checked=[str(path)]
        )

        try:
            # Find project root and resolve dependencies if enabled
            project_root = self._find_project_root(path)
            classpath = None
            
            if self.enable_dependency_resolution and project_root:
                classpath = self._resolve_classpath(project_root)
                if classpath:
                    result.metadata['classpath_resolved'] = True
                    result.metadata['project_type'] = self._detect_project_type(project_root)
            
            # Run javac for syntax checking
            javac_output = self._run_javac(path, project_root, classpath)
            
            if javac_output:
                result.lint_output = f"=== javac ===\n{javac_output}"

            result.metadata['tools_used'] = ['javac']
            result.metadata['project_root'] = str(project_root) if project_root else None
            result.success = True
        except Exception as exc:
            result.success = False
            result.error_message = str(exc)
        finally:
            result.execution_time = time.time() - start_time

        return result

    def _find_project_root(self, file_path: Path) -> Optional[Path]:
        """Find the project root directory by looking for build files."""
        if self._project_root_cache and file_path.is_relative_to(self._project_root_cache):
            return self._project_root_cache
            
        current = file_path.parent
        markers = ['pom.xml', 'build.gradle', 'build.gradle.kts', '.git', 'settings.gradle', 'settings.gradle.kts']
        
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    self._project_root_cache = current
                    return current
            current = current.parent
        
        return None

    def _detect_project_type(self, project_root: Path) -> str:
        """Detect the project type (maven/gradle/local)."""
        if self.project_type != 'auto':
            return self.project_type
            
        if (project_root / 'pom.xml').exists():
            return 'maven'
        elif (project_root / 'build.gradle').exists() or (project_root / 'build.gradle.kts').exists():
            return 'gradle'
        else:
            return 'local'

    @lru_cache(maxsize=1)
    def _resolve_classpath(self, project_root: Path) -> Optional[str]:
        """Resolve project classpath based on project type."""
        if self._classpath_cache and self.cache_dependencies:
            return self._classpath_cache
            
        project_type = self._detect_project_type(project_root)
        classpath = None
        
        if project_type == 'maven':
            classpath = self._resolve_maven_classpath(project_root)
        elif project_type == 'gradle':
            classpath = self._resolve_gradle_classpath(project_root)
        
        # Always check for local JARs as additional dependencies
        local_jars = self._find_local_jars(project_root)
        if local_jars:
            if classpath:
                classpath = f"{classpath}{os.pathsep}{local_jars}"
            else:
                classpath = local_jars
        
        if self.cache_dependencies:
            self._classpath_cache = classpath
            
        return classpath

    def _resolve_maven_classpath(self, project_root: Path) -> Optional[str]:
        """Resolve Maven dependencies using mvn command."""
        try:
            # Create a temporary file for the classpath output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Run Maven to get compile classpath
                cmd = [
                    'mvn', '-q',
                    '-DincludeScope=compile',
                    '-Dmdep.outputFile=' + tmp_path,
                    'dependency:build-classpath'
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and os.path.exists(tmp_path):
                    with open(tmp_path, 'r') as f:
                        classpath = f.read().strip()
                    return classpath if classpath else None
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None

    def _resolve_gradle_classpath(self, project_root: Path) -> Optional[str]:
        """Resolve Gradle dependencies using gradle/gradlew command."""
        try:
            # Create a temporary init script to print classpath
            init_script = """
allprojects {
    tasks.register("printCompileClasspath") {
        doLast {
            def conf = configurations.findByName("compileClasspath")
            if (conf != null) {
                println conf.resolve().collect{ it.absolutePath }.join(File.pathSeparator)
            }
        }
    }
}
"""
            with tempfile.NamedTemporaryFile(mode='w', suffix='.gradle', delete=False) as tmp:
                tmp.write(init_script)
                tmp_path = tmp.name
            
            try:
                # Prefer gradlew if available
                gradle_cmd = './gradlew' if (project_root / 'gradlew').exists() else 'gradle'
                
                cmd = [
                    gradle_cmd, '-q',
                    '-I', tmp_path,
                    'printCompileClasspath'
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Get the last line which should be the classpath
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        classpath = lines[-1].strip()
                        return classpath if classpath and not classpath.startswith('BUILD') else None
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None

    def _find_local_jars(self, project_root: Path) -> Optional[str]:
        """Find JAR files in lib directories."""
        jars = []
        
        for lib_dir in self.lib_dirs:
            lib_path = project_root / lib_dir
            if lib_path.exists() and lib_path.is_dir():
                # Find all JAR files in the directory
                jar_files = list(lib_path.glob('**/*.jar'))
                jars.extend(str(jar) for jar in jar_files)
        
        return os.pathsep.join(jars) if jars else None

    def _find_source_path(self, project_root: Path) -> Optional[str]:
        """Find the source path for the project."""
        source_dirs = []
        
        for source_path in self.source_paths:
            full_path = project_root / source_path
            if full_path.exists() and full_path.is_dir():
                source_dirs.append(str(full_path))
        
        return os.pathsep.join(source_dirs) if source_dirs else None

    def _check_for_module_info(self, project_root: Path) -> bool:
        """Check if the project uses JPMS (has module-info.java)."""
        for source_path in self.source_paths:
            module_info = project_root / source_path / 'module-info.java'
            if module_info.exists():
                return True
        return False

    def _run_javac(self, file_path: Path, project_root: Optional[Path], classpath: Optional[str]) -> str:
        """Run javac with proper classpath and source path configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Try with --release flag first (if enabled)
                if self.use_release_flag:
                    try:
                        return self._execute_javac_command(file_path, project_root, classpath, temp_dir, use_release=True)
                    except Exception as exc:
                        # If --release flag is not supported, retry without it
                        if 'invalid flag' in str(exc) or '--release' in str(exc):
                            return self._execute_javac_command(file_path, project_root, classpath, temp_dir, use_release=False)
                        else:
                            raise exc
                else:
                    return self._execute_javac_command(file_path, project_root, classpath, temp_dir, use_release=False)
            except subprocess.TimeoutExpired:
                raise Exception('javac execution timed out')
            except Exception as exc:
                raise Exception(f'Error running javac: {str(exc)}')

    def _execute_javac_command(self, file_path: Path, project_root: Optional[Path], classpath: Optional[str], 
                               temp_dir: str, use_release: bool = True) -> str:
        """Execute the javac command with specified parameters."""
        cmd = ['javac', '-d', temp_dir]
        
        # Add release version if supported and requested
        if use_release:
            cmd.extend(['--release', self.release_version])
        
        # Add lint options
        cmd.append('-Xlint:all')
        
        # Disable annotation processing for faster checking
        cmd.append('-proc:none')
        
        # Add source path if project root is found
        if project_root:
            source_path = self._find_source_path(project_root)
            if source_path:
                cmd.extend(['--source-path', source_path])
        
        # Add classpath or module-path
        if classpath:
            # Check if using JPMS
            if project_root and self._check_for_module_info(project_root):
                cmd.extend(['--module-path', classpath])
            else:
                cmd.extend(['-classpath', classpath])
        
        # Add custom javac arguments
        cmd.extend(self.javac_args)
        
        # Add the file to compile
        cmd.append(str(file_path))

        completed = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=self.javac_timeout_secs
        )
        
        # Check if command failed due to invalid flag
        if completed.returncode != 0 and use_release and ('invalid flag' in completed.stderr or '--release' in completed.stderr):
            raise Exception(f'Invalid flag error: {completed.stderr}')
        
        # javac outputs errors to stderr
        return completed.stderr.strip()