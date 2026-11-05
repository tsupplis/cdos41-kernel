/* Marks belong to one displayed file list; they never modify disk attributes. */
struct fm_marks { char value[256]; int count; };
int fm_marks_clear();
int fm_marks_key();
int fm_marks_draw();
