import pytest
from autocoder.common import AutoCoderArgs


class TestAutoCoderArgsDefaults:
    """Test all default values of AutoCoderArgs"""

    def test_all_field_defaults(self):
        """Test all field default values by creating instance without parameters"""
        args = AutoCoderArgs()
        
        # Test basic fields
        assert args.request_id is None
        assert args.source_dir == "."
        assert args.git_url is None
        assert args.target_file is None
        assert args.query is None
        assert args.template is None
        assert args.project_type is None
        assert args.execute is None
        assert args.package_name == ""
        assert args.script_path == ""
        
        # Test model fields
        assert args.model == ""
        assert args.chat_model == ""
        assert args.model_max_length == 2000
        assert args.model_max_input_length == 6000
        assert args.vl_model == ""
        assert args.sd_model == ""
        assert args.emb_model == ""
        assert args.code_model == ""
        assert args.generate_rerank_model == ""
        assert args.context_prune_model == ""
        assert args.conversation_prune_model == ""
        assert args.inference_model == ""
        assert args.system_prompt == ""
        assert args.planner_model == ""
        assert args.voice2text_model == ""
        assert args.text2voice_model == ""
        assert args.commit_model == ""
        
        # Test index fields
        assert args.skip_build_index is False
        assert args.skip_filter_index is False
        assert args.index_model == ""
        assert args.index_filter_model == ""
        assert args.index_filter_model_max_input_length == 50*1024
        assert args.index_model_max_length == 0
        assert args.index_model_max_input_length == 0
        assert args.index_model_anti_quota_limit == 0
        
        # Test agentic fields
        assert args.enable_agentic_filter is False
        assert args.enable_agentic_edit is True
        assert args.enable_agentic_auto_approve is False
        assert args.enable_agentic_dangerous_command_check is False
        
        # Test filter fields
        assert args.index_filter_level == 0
        assert args.index_filter_enable_relevance_verification is True
        assert args.index_filter_workers == 1
        assert args.index_filter_file_num == 10
        assert args.index_build_workers == 1
        
        # Test other model fields
        assert args.designer_model == ""
        assert args.file is None
        assert args.ray_address == ""
        assert args.anti_quota_limit == 1
        assert args.print_request is False
        assert args.py_packages == ""
        
        # Test search fields
        assert args.search == ""
        assert args.search_engine == ""
        assert args.search_engine_token == ""
        
        # Test RAG fields
        assert args.rag_url == ""
        assert args.rag_token == ""
        assert args.rag_type == "storage"
        assert args.rag_storage_type == "duckdb"
        assert args.rag_params_max_tokens == 500000
        assert args.rag_doc_filter_relevance == 2
        assert args.rag_context_window_limit == 120000
        assert args.rag_duckdb_vector_dim == 1024
        assert args.rag_duckdb_query_similarity == 0.1
        assert args.rag_duckdb_query_top_k == 10000
        assert args.rag_index_build_workers == 10
        assert args.rag_emb_dim == 1024
        assert args.rag_emb_text_size == 1024
        assert args.local_image_host == ""
        assert args.rag_recall_max_queries == 5
        assert args.rag_qa_conversation_strategy == "multi_round"
        
        # Test relevance and context fields
        assert args.verify_file_relevance_score == 6
        assert args.enable_rag_search is False
        assert args.enable_rag_context is False
        assert args.collection is None
        assert args.collections is None
        
        # Test merge and human fields
        assert args.auto_merge is False
        assert args.human_as_model is False
        assert args.human_model_num == 1
        
        # Test image fields
        assert args.image_file == ""
        assert args.image_mode == "direct"
        assert args.image_max_iter == 1
        
        # Test URL fields
        assert args.urls == ""
        assert args.urls_use_model is False
        assert args.command is None
        assert args.doc_command is None
        assert args.required_exts is None
        assert args.hybrid_index_max_output_tokens == 1000000
        
        # Test various enable fields
        assert args.enable_multi_round_generate is False
        assert args.monitor_mode is False
        assert args.enable_hybrid_index is False
        assert args.rag_build_name is None
        assert args.disable_auto_window is False
        assert args.filter_batch_size == 5
        assert args.disable_segment_reorder is False
        assert args.tokenizer_path is None
        assert args.skip_confirm is False
        assert args.silence is False
        assert args.exclude_files == ""
        assert args.output == ""
        assert args.single_file is False
        assert args.query_prefix is None
        assert args.query_suffix is None
        assert args.from_yaml is None
        assert args.base_dir is None
        assert args.context is None
        assert args.editblock_similarity == 0.9
        assert args.include_project_structure is False
        assert args.new_session is False
        
        # Test prompt and review fields
        assert args.prompt_review is None
        assert args.agent_designer_mode == "svg"
        
        # Test ratio fields
        assert args.full_text_ratio == 0.7
        assert args.segment_ratio == 0.2
        assert args.buff_ratio == 0.1
        
        # Test inference fields
        assert args.disable_inference_enhance is True
        assert args.inference_deep_thought is False
        assert args.inference_slow_without_deep_thought is False
        assert args.inference_compute_precision == 64
        assert args.without_contexts is False
        assert args.skip_events is False
        assert args.data_cells_max_num == 2000
        assert args.generate_times_same_model == 1
        assert args.rank_times_same_model == 1
        
        # Test strategy fields
        assert args.rank_strategy == "file"
        
        # Test action and mode fields
        assert args.action == []
        assert args.enable_global_memory is False
        assert args.product_mode == "lite"
        
        # Test reasoning content fields
        assert args.keep_reasoning_content is False
        assert args.keep_only_reasoning_content is False
        
        # Test code apply fields
        assert args.in_code_apply is False
        assert args.model_filter_path is None
        
        # Test conversation prune fields
        assert args.conversation_prune_safe_zone_tokens == 50*1024
        assert args.conversation_prune_group_size == 4
        assert args.conversation_prune_strategy == "summarize"
        
        # Test context prune fields
        assert args.context_prune_strategy == "extract"
        assert args.context_prune is True
        assert args.context_prune_safe_zone_tokens == 24*1024
        assert args.context_prune_sliding_window_size == 1000
        assert args.context_prune_sliding_window_overlap == 100
        
        # Test command fields
        assert args.auto_command_max_iterations == 10
        assert args.use_shell_commands is True
        assert args.skip_commit is False
        
        # Test beta and reproduction fields
        assert args.enable_beta is False
        assert args.how_to_reproduce is None
        
        # Test URL lists
        assert args.dynamic_urls == []
        assert args.add_updated_urls == []
        
        # Test history fields
        assert args.enable_task_history is False
        assert args.event_file is None
        
        # Test active context fields
        assert args.enable_active_context is False
        assert args.enable_active_context_in_generate is False
        
        # Test generate fields
        assert args.generate_max_rounds == 5
        
        # Test revert fields
        assert args.revert_commit_id is None
        
        # Test auto fix fields
        assert args.enable_auto_fix_lint is False
        assert args.enable_auto_fix_compile is False
        assert args.enable_auto_fix_merge is False
        assert args.auto_fix_lint_max_attempts == 5
        assert args.auto_fix_compile_max_attempts == 5
        assert args.auto_fix_merge_max_attempts == 5
        
        # Test rules fields
        assert args.enable_auto_select_rules is True
        
        # Test shadows fields
        assert args.ignore_clean_shadows is False 