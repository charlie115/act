import Link from "next/link";
import { notFound } from "next/navigation";

import BoardPostClient from "../../../../components/board/BoardPostClient";
import JsonLd from "../../../../components/seo/JsonLd";
import { getBoardPost, stripHtml } from "../../../../lib/api";
import { absoluteUrl, buildMetadata, siteConfig } from "../../../../lib/site";

export async function generateMetadata({ params }) {
  const resolvedParams = await params;
  const postId = resolvedParams?.postId;
  const post = await getBoardPost(postId).catch(() => null);

  if (!post) {
    return buildMetadata({
      title: "Post Not Found",
      description: "요청한 게시글을 찾을 수 없습니다.",
      pathname: `/community-board/post/${postId}`,
      type: "article",
    });
  }

  return buildMetadata({
    title: post.title,
    description: stripHtml(post.content).slice(0, 160),
    pathname: `/community-board/post/${post.id}`,
    type: "article",
  });
}

export default async function CommunityBoardPostPage({ params }) {
  const resolvedParams = await params;
  const postId = resolvedParams?.postId;
  const post = await getBoardPost(postId).catch(() => null);

  if (!post) {
    notFound();
  }

  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    description: stripHtml(post.content).slice(0, 160),
    datePublished: post.date_created,
    author: {
      "@type": "Person",
      name: post.author_profile?.username || "Anonymous",
    },
    publisher: {
      "@type": "Organization",
      name: siteConfig.siteName,
      logo: {
        "@type": "ImageObject",
        url: `${siteConfig.siteUrl}/images/arbicrypto-logo.png`,
      },
    },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": absoluteUrl(`/community-board/post/${post.id}`),
    },
  };

  return (
    <div className="section-stack">
      <JsonLd data={articleJsonLd} />
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <p className="text-lg font-semibold text-ink">게시글 상세</p>
        </div>
        <Link className="ghost-button" href="/community-board">
          목록으로 돌아가기
        </Link>
      </div>
      <BoardPostClient postId={postId} />
    </div>
  );
}
