select 
	cast(t."date" as DATE),
	t."comment",
	e."name" as exercise_name,
	s.overall_order,
	s.exercise_order,
	s.weight,
	s.repetitions,
--	training
	sum(s.weight * s.repetitions) over(partition by t.id, e.id) as training_exercise_weight_sum,
	sum(s.repetitions) over(partition by t.id, e.id) as training_exercise_repetitions_sum,
	count(*) over(partition by t.id, e.id) as training_exercise_sets_count,
	count(*) over(partition by t.id) as training_sets_count,
--	exercise_all
	sum(s.weight * s.repetitions) over(partition by e.id) as exercise_all_weight_sum,
	sum(s.repetitions) over(partition by e.id) as exercise_all_repetitions_sum,
	count(*) over(partition by e.id) as exercise_sets_count,
--	exercise_rank
	uer.rating_value as exercise_rank_value,
	r."name" as exercise_rank_name,
	er."level" as exercise_rank_star_count,
	REPEAT('⭐', er."level") as exercise_rank_star_level,
--	all
	count(*) over() as all_sets_count
from training t
	join "set" s on s.training_id = t.id
	join exercise e on e.id = s.exercise_id 
	left join user_exercise_rating uer on uer.exercise_id = s.exercise_id and uer.user_id = t.user_id
	join exercise_rank er on er.id  = uer.exercise_rank_id
	join "rank" r on r.id = er.rank_id
where t.user_id = 409218520
order by cast(t."date" as DATE), e."name", s.exercise_order