-- Grain: one book. Votes are not sales or unique readers.
SELECT COUNT(DISTINCT bookID) AS catalogue_books,
       SUM(ratings_count) AS total_ratings,
       ROUND(AVG(average_rating), 6) AS average_book_rating,
       ROUND(SUM(average_rating * ratings_count) / NULLIF(SUM(ratings_count), 0), 6)
         AS rating_weighted_by_votes
FROM FactBooks;

SELECT SUM(f.ratings_count) AS inflated_total_after_author_join
FROM FactBooks f JOIN BridgeAuthorBook b USING(bookID);

SELECT SUM(f.ratings_count) AS ratings_first_author
FROM FactBooks f WHERE EXISTS (
  SELECT 1 FROM BridgeAuthorBook b WHERE b.bookID=f.bookID
  AND b.authorID=(SELECT MIN(authorID) FROM DimAuthors));
